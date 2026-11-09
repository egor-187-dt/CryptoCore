"""Generate a nonsecret STS test sample using the application's actual CSPRNG."""

import argparse
import hashlib
import json
from pathlib import Path

from cryptocore.csprng import generate_random_bytes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/nist/random.bin"))
    parser.add_argument("--bytes", type=int, default=12_500_000, dest="size")
    parser.add_argument("--metadata", type=Path, default=Path("verification/nist_data.json"))
    args = parser.parse_args()
    if args.size < 1:
        parser.error("--bytes must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    checksum = hashlib.sha256()
    with args.output.open("wb") as stream:
        remaining = args.size
        while remaining:
            data = generate_random_bytes(min(65536, remaining))
            stream.write(data)
            checksum.update(data)
            remaining -= len(data)
    metadata = {"path": args.output.as_posix(), "bytes": args.size,
                "sha256": checksum.hexdigest(), "generator": "cryptocore.csprng.generate_random_bytes -> os.urandom",
                "planned_sequence_bits": 1_000_000, "planned_sequences": args.size * 8 // 1_000_000,
                "sts_run": False}
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
