"""IV-framed files and both OpenSSL compatibility directions for each mode."""

from contextlib import redirect_stderr
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from cryptocore.cli import main
from cryptocore.file_io import transform_file
from cryptocore.modes import create_context
from tests.support import KEY, command, openssl_path, run_cli

IV = bytes(range(16))


class IVFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="CryptoCore IV кириллица ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source, self.cipher, self.restored = [self.root/name for name in ("вход p", "шифр c", "результат r")]

    def test_all_mode_cli_roundtrips_and_format(self):
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            for data in (b"", bytes(1), bytes(15), bytes(16), bytes(17), bytes(31), bytes(32), bytes(range(256)), "Текст".encode()):
                with self.subTest(mode=mode, length=len(data)):
                    self.source.write_bytes(data)
                    result = run_cli(*command(mode, True, self.source, self.cipher))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    framed = self.cipher.read_bytes()
                    expected_length = ((len(data)//16)+1)*16 if mode == "cbc" else len(data)
                    self.assertEqual(len(framed), 16+expected_length)
                    self.assertEqual(run_cli(*command(mode, False, self.cipher, self.restored)).returncode, 0)
                    self.assertEqual(self.restored.read_bytes(), data)
                    raw = self.root / "raw c"
                    raw.write_bytes(framed[16:])
                    result = run_cli(*(command(mode, False, raw, self.restored)+["--iv", framed[:16].hex().upper()]))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(self.restored.read_bytes(), data)

    def test_iv_generation_source_and_prefix(self):
        self.source.write_bytes(b"partial\0\xff")
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            with patch("cryptocore.cli.csprng.generate_random_bytes", return_value=IV) as rng:
                self.assertEqual(main(command(mode, True, self.source, self.cipher)), 0)
                rng.assert_called_once_with(16)
            self.assertEqual(self.cipher.read_bytes()[:16], IV)
        with patch("cryptocore.cli.csprng.generate_random_bytes") as rng:
            self.assertEqual(main(command("ecb", True, self.source, self.cipher)), 0)
            rng.assert_not_called()

    def test_iv_argument_rules(self):
        self.source.write_bytes(bytes(32))
        for mode in ("ecb", "cbc", "cfb", "ofb", "ctr"):
            result = run_cli(*(command(mode, True, self.source, self.cipher)+["--iv", IV.hex()]))
            self.assertEqual(result.returncode, 2)
            for value in ("", "xx"*16, "00", "00 "*16, "00"*17):
                result = run_cli(*(command(mode, False, self.source, self.cipher)+["--iv", value]))
                self.assertEqual(result.returncode, 2)
        self.assertEqual(run_cli(*(command("ecb", False, self.source, self.cipher)+["--iv", IV.hex()])).returncode, 2)

    def test_short_iv_and_cbc_corruption_preserve_output(self):
        self.restored.write_bytes(b"KEEP")
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            for size in (0, 1, 15):
                self.cipher.write_bytes(bytes(size))
                result = run_cli(*command(mode, False, self.cipher, self.restored))
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stderr)
                self.assertEqual(self.restored.read_bytes(), b"KEEP")
        for size in (16, 17, 31, 33):
            self.cipher.write_bytes(bytes(size))
            self.assertEqual(run_cli(*command("cbc", False, self.cipher, self.restored)).returncode, 1)
            self.assertEqual(self.restored.read_bytes(), b"KEEP")
        self.assertEqual(list(self.root.glob(".cryptocore-*.tmp")), [])

    def test_rng_failure_preserves_output(self):
        self.source.write_bytes(b"data")
        self.cipher.write_bytes(b"KEEP")
        with patch("cryptocore.cli.csprng.generate_random_bytes", side_effect=OSError("RNG unavailable")):
            with redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(main(command("cbc", True, self.source, self.cipher)), 1)
                self.assertIn("RNG", errors.getvalue())
        self.assertEqual(self.cipher.read_bytes(), b"KEEP")

    def test_file_chunks_all_modes(self):
        plain = bytes(range(256))*3 + b"tail"
        self.source.write_bytes(plain)
        for mode in ("cbc", "cfb", "ofb", "ctr"):
            expected = None
            for chunk in (1, 7, 15, 16, 17, 65536):
                transform_file(self.source, self.cipher, lambda _: create_context(mode, KEY, True, IV), chunk_size=chunk, output_prefix=IV)
                framed = self.cipher.read_bytes()
                if expected is None:
                    expected = framed
                self.assertEqual(framed, expected)
                transform_file(self.cipher, self.restored, lambda header: create_context(mode, KEY, False, header), chunk_size=chunk, header_size=16)
                self.assertEqual(self.restored.read_bytes(), plain)


class ModesOpenSSLTests(unittest.TestCase):
    def check_mode(self, mode):
        executable = openssl_path()
        if executable is None:
            self.skipTest("OpenSSL executable unavailable")
        for plain in (b"", bytes(1), bytes(15), bytes(16), bytes(17), bytes(range(256))):
            with self.subTest(mode=mode, length=len(plain)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, framed, raw, restored, reference = [root/name for name in ("p", "framed", "raw", "r", "ref")]
                source.write_bytes(plain)
                result = run_cli(*command(mode, True, source, framed))
                self.assertEqual(result.returncode, 0, result.stderr)
                data = framed.read_bytes()
                iv = data[:16]
                raw.write_bytes(data[16:])
                base = [executable, "enc", "-aes-128-"+mode, "-nosalt", "-K", KEY.hex(), "-iv", iv.hex()]
                result = subprocess.run(base+["-d", "-in", str(raw), "-out", str(restored)], capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(restored.read_bytes(), plain)
                result = subprocess.run(base+["-in", str(source), "-out", str(reference)], capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(reference.read_bytes(), raw.read_bytes())
                result = run_cli(*(command(mode, False, reference, restored)+["--iv", iv.hex()]))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(restored.read_bytes(), plain)

    def test_cbc_both_directions(self):
        self.check_mode("cbc")

    def test_cfb128_both_directions(self):
        self.check_mode("cfb")

    def test_ofb_both_directions(self):
        self.check_mode("ofb")

    def test_ctr_both_directions(self):
        self.check_mode("ctr")
