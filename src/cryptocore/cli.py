"""Command-line validation and orchestration; errors never expose keys."""

import argparse
import re
import sys

from .file_io import transform_file
from .modes import MODE_NAMES, create_context
from . import csprng


def hex16(value: str) -> bytes:
    """Parse exactly 16 bytes of hex, without whitespace or text fallback."""
    if re.fullmatch(r"[0-9a-fA-F]{32}", value) is None:
        raise argparse.ArgumentTypeError("Expected exactly 32 hexadecimal characters (16 bytes)")
    return bytes.fromhex(value)


def build_parser() -> argparse.ArgumentParser:
    """Construct the supported CLI; reject abbreviations and unknown flags."""
    parser = argparse.ArgumentParser(prog="cryptocore", allow_abbrev=False)
    parser.add_argument("--algorithm", required=True, choices=("aes",))
    parser.add_argument("--mode", required=True, choices=MODE_NAMES)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--encrypt", action="store_true")
    operation.add_argument("--decrypt", action="store_true")
    parser.add_argument("--key", type=hex16, help="16-byte hex key; generated when omitted for encryption")
    parser.add_argument("--iv", type=hex16, help="Decryption only: input is raw ciphertext without IV prefix")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Return 0 on success, 1 for operation failures, argparse uses 2 for usage."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.iv is not None and (args.encrypt or args.mode == "ecb"):
        parser.error("--iv is accepted only for non-ECB decryption")
    if args.decrypt and args.key is None:
        parser.error("--key is required for decryption")
    try:
        key = args.key
        if key is None:
            key = csprng.generate_random_bytes(16)
            print(f"[INFO] Generated random key: {key.hex()}", flush=True)
        elif len(set(key)) == 1 or all(
            (key[index] - key[index-1]) % 256 == 1 for index in range(1, 16)
        ) or all((key[index-1] - key[index]) % 256 == 1 for index in range(1, 16)):
            print("cryptocore: warning: supplied key has a weak repeating/sequential pattern", file=sys.stderr)
        iv = args.iv
        prefix = b""
        header_size = 0
        if args.mode != "ecb":
            if args.encrypt:
                iv = csprng.generate_random_bytes(16)
                prefix = iv
            elif iv is None:
                header_size = 16
        transform_file(
            args.input, args.output,
            lambda header: create_context(args.mode, key, args.encrypt, header if header_size else iv),
            header_size=header_size, output_prefix=prefix,
        )
    except (OSError, ValueError) as error:
        print(f"cryptocore: error: {error}", file=sys.stderr)
        return 1
    return 0
