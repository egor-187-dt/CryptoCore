"""Shared deterministic fixtures and executable discovery (no shell commands)."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
METRICS = {}
CLI = Path(sys.executable).parent / ("cryptocore.exe" if os.name == "nt" else "cryptocore")
KEY = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
PLAINTEXT = bytes.fromhex(
    "6bc1bee22e409f96e93d7e117393172a"
    "ae2d8a571e03ac9c9eb76fac45af8e51"
    "30c81c46a35ce411e5fbc1191a0a52ef"
    "f69f2445df4f9b17ad2b417be66c3710"
)
ECB_CIPHER = bytes.fromhex(
    "3ad77bb40d7a3660a89ecaf32466ef97"
    "f5d3d58503b9699de785895a96fdbaaf"
    "43b1cd7f598ece23881b00e3ed030688"
    "7b0c785e27e8ad3f8223207104725dd4"
)


def openssl_path() -> str | None:
    """Use explicit setting, PATH or the OpenSSL shipped by Git for Windows."""
    explicit = os.environ.get("OPENSSL_EXE")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    found = shutil.which("openssl")
    if found:
        return found
    for relative in ("Git/usr/bin/openssl.exe", "Git/mingw64/bin/openssl.exe"):
        candidate = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / relative
        if candidate.is_file():
            return str(candidate)
    return None


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run the actual installed console entry point, capturing both streams."""
    return subprocess.run([str(CLI), *args], capture_output=True, timeout=60)


def command(mode: str, encrypt: bool, source: Path, dest: Path, key: bytes = KEY) -> list[str]:
    """Build a fully specified CLI command without quoting or shell expansion."""
    return ["--algorithm", "aes", "--mode", mode,
            "--encrypt" if encrypt else "--decrypt", "--key", key.hex(),
            "--input", str(source), "--output", str(dest)]


def crypt(context, data: bytes, chunk_size: int) -> bytes:
    """Feed a small unit-test fixture incrementally."""
    return b"".join(context.update(data[i:i + chunk_size])
                    for i in range(0, len(data), chunk_size)) + context.finalize()
