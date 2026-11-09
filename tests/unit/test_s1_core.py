"""FIPS 197 / SP 800-38A ECB known answers and PKCS#7 boundaries."""

import unittest

from cryptocore.aes import AES128, decrypt_block, encrypt_block
from cryptocore.modes.ecb import ECB
from cryptocore.padding import pad, unpad
from tests.support import ECB_CIPHER, KEY, PLAINTEXT, crypt


class AESBlockTests(unittest.TestCase):
    def test_fips197_known_answer(self):
        key = bytes(range(16))
        plain = bytes.fromhex("00112233445566778899aabbccddeeff")
        cipher = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
        self.assertEqual(encrypt_block(key, plain), cipher)
        self.assertEqual(decrypt_block(key, cipher), plain)

    def test_sp800_38a_all_ecb_blocks(self):
        aes = AES128(KEY)
        for start in range(0, 64, 16):
            with self.subTest(block=start // 16):
                self.assertEqual(aes.encrypt_block(PLAINTEXT[start:start+16]), ECB_CIPHER[start:start+16])
                self.assertEqual(aes.decrypt_block(ECB_CIPHER[start:start+16]), PLAINTEXT[start:start+16])

    def test_reject_invalid_keys(self):
        for value in (b"", b"x" * 15, b"x" * 17, b"x" * 24, b"x" * 32, "x" * 16):
            with self.subTest(value_type=type(value), length=len(value)):
                with self.assertRaises(ValueError):
                    AES128(value)

    def test_reject_invalid_blocks(self):
        for data in (b"", b"x" * 15, b"x" * 17, "x" * 16):
            for operation in (AES128(KEY).encrypt_block, AES128(KEY).decrypt_block):
                with self.assertRaises(ValueError):
                    operation(data)


class PaddingTests(unittest.TestCase):
    def test_every_padding_length(self):
        for length in range(65):
            with self.subTest(length=length):
                plain = bytes(range(length))
                padded = pad(plain)
                count = 16 - length % 16
                self.assertEqual(padded, plain + bytes([count]) * count)
                self.assertEqual(unpad(padded), plain)

    def test_invalid_padding(self):
        invalid = [b"", b"x", b"x" * 15, b"x" * 17,
                   b"x" * 15 + b"\0", b"x" * 15 + b"\x11",
                   b"x" * 14 + b"\x01\x02"]
        for data in invalid:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    unpad(data)

    def test_size_and_type_validation(self):
        for size in (0, -1, 256, True, 1.5):
            for operation in (pad, unpad):
                with self.assertRaises(ValueError):
                    operation(b"x", size)
        for operation in (pad, unpad):
            with self.assertRaises(TypeError):
                operation("text")


class ECBTests(unittest.TestCase):
    def test_nist_file_prefix_and_decryption(self):
        encrypted = crypt(ECB(KEY, True), PLAINTEXT, 7)
        self.assertEqual(encrypted[:64], ECB_CIPHER)
        self.assertEqual(len(encrypted), 80)
        self.assertEqual(crypt(ECB(KEY, False), encrypted, 11), PLAINTEXT)

    def test_all_lengths_and_chunk_boundaries(self):
        for length in (0, 1, 15, 16, 17, 31, 32, 33, 127, 256, 1025):
            plain = bytes(i % 256 for i in range(length))
            reference = crypt(ECB(KEY, True), plain, 65536)
            for chunk in (1, 7, 15, 16, 17, 31, 64, 65536):
                with self.subTest(length=length, chunk=chunk):
                    self.assertEqual(crypt(ECB(KEY, True), plain, chunk), reference)
                    self.assertEqual(crypt(ECB(KEY, False), reference, chunk), plain)

    def test_invalid_ciphertext_lengths(self):
        for length in (0, 1, 15, 17, 31, 33):
            with self.assertRaises(ValueError):
                crypt(ECB(KEY, False), bytes(length), 7)

    def test_lifecycle_and_types(self):
        for encrypt in (True, False):
            context = ECB(KEY, encrypt)
            self.assertEqual(context.update(b""), b"")
            with self.assertRaises(TypeError):
                context.update("text")
            if encrypt:
                context.finalize()
            else:
                with self.assertRaises(ValueError):
                    context.finalize()
            for operation in (lambda: context.update(b""), context.finalize):
                with self.assertRaises(ValueError):
                    operation()
        with self.assertRaises(TypeError):
            ECB(KEY, 1)
