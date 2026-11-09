"""NIST KAT, independent library oracles and partial-chunk state checks."""

import json
import tracemalloc
import unittest

from Crypto.Cipher import AES

from cryptocore.modes import create_context
from cryptocore.modes.ctr import CTR
from tests.support import KEY, PLAINTEXT, ROOT, METRICS, crypt

VECTORS = json.loads((ROOT / "tests/vectors/sp800_38a_aes128.json").read_text())
IV = bytes.fromhex(VECTORS["iv"])


class ModeKATTests(unittest.TestCase):
    def check_vector(self, mode):
        iv = bytes.fromhex(VECTORS["ctr_iv"]) if mode == "ctr" else IV
        expected = bytes.fromhex(VECTORS["ciphertexts"][mode])
        result = crypt(create_context(mode, KEY, True, iv), PLAINTEXT, 7)
        self.assertEqual(result[:64], expected)
        if mode != "cbc":
            self.assertEqual(len(result), 64)
            self.assertEqual(crypt(create_context(mode, KEY, False, iv), expected, 11), PLAINTEXT)
        else:
            # Independently construct just the trailing PKCS#7 block from known C4.
            final = AES.new(KEY, AES.MODE_ECB).encrypt(bytes(a ^ 16 for a in expected[-16:]))
            self.assertEqual(result[64:], final)
            self.assertEqual(crypt(create_context(mode, KEY, False, iv), expected + final, 11), PLAINTEXT)

    def test_cbc_nist(self):
        self.check_vector("cbc")

    def test_cfb128_nist(self):
        self.check_vector("cfb")

    def test_ofb_nist(self):
        self.check_vector("ofb")

    def test_ctr_nist(self):
        self.check_vector("ctr")


class ModeBoundaryTests(unittest.TestCase):
    def test_independent_oracle_and_chunks(self):
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            for length in (0, 1, 2, 15, 16, 17, 31, 32, 33, 127, 255, 1025):
                plain = bytes(i % 256 for i in range(length))
                if mode == "cbc":
                    padding = 16 - len(plain) % 16
                    expected = AES.new(KEY, AES.MODE_CBC, iv=IV).encrypt(plain + bytes([padding])*padding)
                elif mode == "cfb":
                    expected = AES.new(KEY, AES.MODE_CFB, iv=IV, segment_size=128).encrypt(plain)
                elif mode == "ofb":
                    expected = AES.new(KEY, AES.MODE_OFB, iv=IV).encrypt(plain)
                else:
                    expected = AES.new(KEY, AES.MODE_CTR, nonce=b"", initial_value=int.from_bytes(IV, "big")).encrypt(plain)
                for chunk in (1, 7, 15, 16, 17, 63, 65536):
                    with self.subTest(mode=mode, length=length, chunk=chunk):
                        self.assertEqual(crypt(create_context(mode, KEY, True, IV), plain, chunk), expected)
                        self.assertEqual(crypt(create_context(mode, KEY, False, IV), expected, chunk), plain)

    def test_invalid_iv_and_mode(self):
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            for iv in (None, b"", bytes(15), bytes(17), "0"*16):
                with self.assertRaises(ValueError):
                    create_context(mode, KEY, True, iv)
        with self.assertRaises(ValueError):
            create_context("unknown", KEY, True, IV)
        with self.assertRaises(ValueError):
            create_context("ecb", KEY, True, IV)

    def test_stream_lifecycle(self):
        for mode in ("cfb", "ofb", "ctr"):
            for encrypt in (True, False):
                context = create_context(mode, KEY, encrypt, IV)
                self.assertEqual(context.update(b""), b"")
                with self.assertRaises(TypeError):
                    context.update("text")
                self.assertEqual(context.finalize(), b"")
                for operation in (context.finalize, lambda: context.update(b"x")):
                    with self.assertRaises(ValueError):
                        operation()
            with self.assertRaises(TypeError):
                create_context(mode, KEY, 1, IV)

    def test_counter_carry_and_exhaustion(self):
        iv = bytes.fromhex("0000000000000000000000000000ffff")
        oracle = AES.new(KEY, AES.MODE_CTR, nonce=b"", initial_value=int.from_bytes(iv, "big"))
        self.assertEqual(crypt(CTR(KEY, iv, True), bytes(49), 7), oracle.encrypt(bytes(49)))
        context = CTR(KEY, b"\xff"*16, True)
        expected = AES.new(KEY, AES.MODE_ECB).encrypt(b"\xff"*16)
        self.assertEqual(context.update(bytes(1)) + context.update(bytes(15)), expected)
        with self.assertRaisesRegex(ValueError, "exhausted"):
            context.update(b"x")

    def test_new_modes_bounded_state_memory(self):
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            for encrypt in (True, False):
                context = create_context(mode, KEY, encrypt, IV)
                tracemalloc.start()
                try:
                    for _ in range(128):
                        context.update(bytes(4096))
                    peak = tracemalloc.get_traced_memory()[1]
                finally:
                    tracemalloc.stop()
                self.assertLess(peak, 128*1024, (mode, encrypt, peak))
                METRICS[f"{mode}_{'encrypt' if encrypt else 'decrypt'}_peak_bytes_512KiB"] = peak
