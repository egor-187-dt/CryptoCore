"""Final audit: Windows sharing errors, partial IO and source invariants."""

import ast
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptocore.file_io import transform_file
from cryptocore.modes.ecb import ECB
from tests.support import KEY, ROOT, command, run_cli


class AtomicIOAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="CryptoCore audit ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source, self.destination = self.root / "input", self.root / "output"
        self.source.write_bytes(bytes(range(80)))
        self.destination.write_bytes(b"KEEP")

    def check_preserved(self):
        self.assertEqual(self.source.read_bytes(), bytes(range(80)))
        self.assertEqual(self.destination.read_bytes(), b"KEEP")
        self.assertEqual(list(self.root.glob(".cryptocore-*.tmp")), [])

    @unittest.skipUnless(os.name == "nt", "Windows sharing semantics")
    def test_actual_windows_input_and_output_locks(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                      wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel.CloseHandle.restype = wintypes.BOOL
        for path in (self.source, self.destination):
            handle = kernel.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)
            self.assertNotEqual(handle, wintypes.HANDLE(-1).value, ctypes.get_last_error())
            try:
                result = run_cli(*command("ecb", True, self.source, self.destination))
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stderr)
                self.assertEqual(result.stdout, b"")
            finally:
                kernel.CloseHandle(handle)
            self.check_preserved()

    def test_partial_write_error_preserves_files(self):
        original = tempfile.NamedTemporaryFile

        class FaultyOutput:
            def __init__(self, stream):
                self.stream = stream

            def __getattr__(self, name):
                return getattr(self.stream, name)

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def write(self, data):
                if data:
                    self.stream.write(data[:3])
                    raise OSError("injected disk-full after partial write")
                return self.stream.write(data)

        with patch("cryptocore.file_io.tempfile.NamedTemporaryFile", side_effect=lambda *a, **kw: FaultyOutput(original(*a, **kw))):
            with self.assertRaisesRegex(OSError, "partial write"):
                transform_file(self.source, self.destination, lambda _: ECB(KEY, True), chunk_size=16)
        self.check_preserved()

    def test_midstream_read_error_preserves_files(self):
        original = Path.open

        class FaultyInput:
            def __init__(self, stream):
                self.stream, self.calls = stream, 0

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def read(self, size):
                self.calls += 1
                if self.calls == 2:
                    raise OSError("injected midstream read error")
                return self.stream.read(size)

        def open_input(path, *args, **kwargs):
            stream = original(path, *args, **kwargs)
            return FaultyInput(stream) if path == self.source else stream

        with patch("cryptocore.file_io.Path.open", new=open_input):
            with self.assertRaisesRegex(OSError, "midstream read"):
                transform_file(self.source, self.destination, lambda _: ECB(KEY, True), chunk_size=16)
        self.check_preserved()


class SourceAuditTests(unittest.TestCase):
    def test_original_requirement_bytes_preserved(self):
        baseline = json.loads((ROOT / "verification/sprint1.json").read_text(encoding="utf-8"))
        originals = {path: digest for path, digest in baseline["source_sha256"].items() if path.startswith("requirements/")}
        self.assertEqual(len(originals), 9)
        for path, digest in originals.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)

    def test_only_single_block_library_aes_and_os_rng(self):
        calls = []
        for path in (ROOT / "src/cryptocore").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any(alias.name == "random" for alias in node.names), path)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "random", path)
                    if node.module and node.module.startswith("Crypto"):
                        self.assertEqual(node.module, "Crypto.Cipher")
                        self.assertEqual([alias.name for alias in node.names], ["AES"])
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "AES":
                        self.assertEqual(node.func.attr, "new")
                        self.assertIsInstance(node.args[1], ast.Attribute)
                        self.assertEqual(node.args[1].attr, "MODE_ECB")
                        calls.append(path.name)
        self.assertEqual(calls, ["aes.py"])
        for future in ("hash", "mac", "kdf", "aead", "modes/gcm.py"):
            self.assertFalse((ROOT / "src/cryptocore" / future).exists())
