"""Actual console invocation, Windows paths, atomic output and bounded memory."""

from contextlib import redirect_stderr
import io
import os
from pathlib import Path
import subprocess
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

from cryptocore.cli import main
from cryptocore.file_io import transform_file
from cryptocore.modes.ecb import ECB
from tests.support import CLI, KEY, ROOT, METRICS, command, openssl_path, run_cli


class CLIIOTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="CryptoCore кириллица ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source, self.dest = self.root / "вход файл.bin", self.root / "выход файл.bin"
        self.source.write_bytes(b"existing input\x00\xff")

    def assert_clean(self):
        self.assertEqual(list(self.root.glob(".cryptocore-*.tmp")), [])

    def test_entrypoint_and_roundtrip(self):
        self.assertTrue(CLI.is_file())
        for data in (b"", "Привет, мир!".encode(), bytes(range(256)), *[bytes(n) for n in (1,15,16,17,31,32)]):
            with self.subTest(length=len(data)):
                self.source.write_bytes(data)
                result = run_cli(*command("ecb", True, self.source, self.dest))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b"")
                restored = self.root / "restored.bin"
                result = run_cli(*command("ecb", False, self.dest, restored))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(restored.read_bytes(), data)
                self.assertEqual(self.source.read_bytes(), data)
        self.assert_clean()

    def test_missing_and_conflicting_arguments(self):
        base = command("ecb", True, self.source, self.dest)
        # S3 intentionally makes the encryption key optional (E01).
        for flag in ("--algorithm", "--mode", "--input", "--output"):
            args = base.copy()
            position = args.index(flag)
            del args[position:position+2]
            result = run_cli(*args)
            self.assertNotEqual(result.returncode, 0, flag)
            self.assertTrue(result.stderr)
        for args in ([arg for arg in base if arg != "--encrypt"], base + ["--decrypt"]):
            result = run_cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(result.stderr)
        self.assertFalse(self.dest.exists())

    def test_invalid_values_and_future_features(self):
        base = command("ecb", True, self.source, self.dest)
        for flag, values in (("--key", ("", "00", "g"*32, "00 "*16, "0"*31, "00"*24, "00"*32)),
                             ("--mode", ("gcm", "unknown")), ("--algorithm", ("sha256", "aes256"))):
            for value in values:
                args = base.copy()
                args[args.index(flag)+1] = value
                result = run_cli(*args)
                self.assertEqual(result.returncode, 2, (flag, len(value)))
                if flag == "--key" and value:
                    self.assertNotIn(value.encode(), result.stderr, "Secrets must not appear in errors")
        for extra in (["--aad", "aa"], ["--unknown"], ["--alg", "aes"]):
            self.assertEqual(run_cli(*(base + extra)).returncode, 2)

    def test_file_errors_preserve_existing_output(self):
        self.dest.write_bytes(b"KEEP")
        for source in (self.root / "missing", self.root):
            result = run_cli(*command("ecb", True, source, self.dest))
            self.assertEqual(result.returncode, 1)
            self.assertTrue(result.stderr)
            self.assertEqual(self.dest.read_bytes(), b"KEEP")
        for output in (self.root / "missing" / "out", self.root):
            result = run_cli(*command("ecb", True, self.source, output))
            self.assertEqual(result.returncode, 1)
            self.assertTrue(result.stderr)
        self.assert_clean()

    def test_padding_failure_preserves_or_does_not_create_output(self):
        from cryptocore.aes import encrypt_block
        # Encrypt a block with intentionally invalid PKCS#7, not a probabilistic bit flip.
        self.source.write_bytes(encrypt_block(KEY, b"x"*15 + b"\0"))
        for exists in (False, True):
            if exists:
                self.dest.write_bytes(b"KEEP")
            result = run_cli(*command("ecb", False, self.source, self.dest))
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, b"")
            self.assertTrue(result.stderr)
            self.assertEqual(self.dest.read_bytes() if exists else self.dest.exists(), b"KEEP" if exists else False)
            self.assert_clean()

    def test_identical_paths_and_hardlinks_rejected(self):
        before = self.source.read_bytes()
        self.assertEqual(run_cli(*command("ecb", True, self.source, self.source)).returncode, 1)
        os.link(self.source, self.dest)
        self.assertEqual(run_cli(*command("ecb", True, self.source, self.dest)).returncode, 1)
        self.assertEqual(self.source.read_bytes(), before)

    def test_replace_and_sync_failures_preserve_output(self):
        self.dest.write_bytes(b"KEEP")
        for target in ("cryptocore.file_io.os.replace", "cryptocore.file_io.os.fsync"):
            with patch(target, side_effect=PermissionError("injected access denied")):
                with self.assertRaises(PermissionError):
                    transform_file(self.source, self.dest, lambda _: ECB(KEY, True))
            self.assertEqual(self.dest.read_bytes(), b"KEEP")
            self.assert_clean()

    def test_read_and_write_failures(self):
        self.dest.write_bytes(b"KEEP")
        for target in ("cryptocore.file_io.Path.open", "cryptocore.file_io.tempfile.NamedTemporaryFile"):
            with patch(target, side_effect=PermissionError("injected access denied")):
                with redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(main(command("ecb", True, self.source, self.dest)), 1)
                    self.assertIn("access denied", errors.getvalue())
            self.assertEqual(self.dest.read_bytes(), b"KEEP")
            self.assert_clean()

    def test_midstream_failure_preserves_output(self):
        class Broken:
            def update(self, data):
                raise OSError("injected read/transform failure")
        self.dest.write_bytes(b"KEEP")
        with self.assertRaises(OSError):
            transform_file(self.source, self.dest, lambda _: Broken())
        self.assertEqual(self.dest.read_bytes(), b"KEEP")
        self.assert_clean()

    def test_chunk_size_validation(self):
        for chunk in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                transform_file(self.source, self.dest, lambda _: ECB(KEY, True), chunk_size=chunk)

    def test_file_chunk_independence(self):
        self.source.write_bytes(bytes(range(256))*4)
        results = []
        for chunk in (1, 7, 15, 16, 17, 4096, 65536):
            transform_file(self.source, self.dest, lambda _: ECB(KEY, True), chunk_size=chunk)
            results.append(self.dest.read_bytes())
        self.assertTrue(all(item == results[0] for item in results))

    def test_bounded_memory(self):
        peaks = []
        for size in (256*1024, 4*1024*1024):
            with self.source.open("wb") as stream:
                for _ in range(size // 65536):
                    stream.write(bytes(65536))
            tracemalloc.start()
            try:
                transform_file(self.source, self.dest, lambda _: ECB(KEY, True))
                peaks.append(tracemalloc.get_traced_memory()[1])
            finally:
                tracemalloc.stop()
        self.assertLess(max(peaks), 1024*1024, peaks)
        self.assertLess(peaks[1] - peaks[0], 256*1024, peaks)
        METRICS["ecb_file_peak_bytes_256KiB_4MiB"] = peaks


class PackagingTests(unittest.TestCase):
    def test_git_packaging_and_readme(self):
        import importlib.metadata
        import tomllib
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertEqual(project["project"]["scripts"]["cryptocore"], "cryptocore.cli:main")
        self.assertEqual(importlib.metadata.version("pycryptodome"), "4.3.0")
        self.assertIn("CryptoCore", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT, capture_output=True).stdout.strip(), b"true")
        ignored = subprocess.run(["git", "check-ignore", "--no-index", ".venv/test", ".idea/test", "src/cryptocore/aes.py", "tests/vectors/test.bin"], cwd=ROOT, capture_output=True)
        self.assertEqual(set(ignored.stdout.decode().splitlines()), {".venv/test", ".idea/test"})


class ECBOpenSSLTests(unittest.TestCase):
    def test_ecb_both_directions(self):
        executable = openssl_path()
        if executable is None:
            self.skipTest("OpenSSL executable unavailable")
        for data in (b"", bytes(range(256)), b"not aligned\x00\xff"):
            with self.subTest(length=len(data)), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source, cipher, restored, reference = [root / name for name in ("p", "c", "r", "ref")]
                source.write_bytes(data)
                self.assertEqual(run_cli(*command("ecb", True, source, cipher)).returncode, 0)
                result = subprocess.run([executable, "enc", "-aes-128-ecb", "-nosalt", "-K", KEY.hex(), "-in", str(source), "-out", str(reference)], capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(cipher.read_bytes(), reference.read_bytes())
                result = subprocess.run([executable, "enc", "-aes-128-ecb", "-d", "-nosalt", "-K", KEY.hex(), "-in", str(cipher), "-out", str(restored)], capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(restored.read_bytes(), data)
                self.assertEqual(run_cli(*command("ecb", False, reference, restored)).returncode, 0)
                self.assertEqual(restored.read_bytes(), data)
