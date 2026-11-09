"""Binary streaming and atomic publication; failed operations preserve output."""

import os
from pathlib import Path
import tempfile
from typing import Callable, Protocol


class CipherContext(Protocol):
    """Minimal operation interface; implementations have bounded tail state."""

    def update(self, data: bytes) -> bytes: ...
    def finalize(self) -> bytes: ...


def transform_file(
    input_path: str | Path,
    output_path: str | Path,
    context_factory: Callable[[bytes], CipherContext],
    *,
    chunk_size: int = 65536,
    header_size: int = 0,
    output_prefix: bytes = b"",
) -> None:
    """Stream through a context, publish only after finalization and fsync.

    The optional header is read from the same input handle as the data.
    A temporary file in the destination directory permits atomic os.replace.
    Existing input/output aliases (including hard links) are rejected.
    """
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if type(header_size) is not int or header_size < 0:
        raise ValueError("header_size must be a nonnegative integer")
    source, destination = Path(input_path), Path(output_path)
    if source.resolve() == destination.resolve() or (
        destination.exists() and os.path.samefile(source, destination)
    ):
        raise ValueError("Input and output must be different files")
    temporary = None
    try:
        with source.open("rb") as incoming:
            header = incoming.read(header_size) if header_size else b""
            if len(header) != header_size:
                raise ValueError(f"Input is too short: expected {header_size}-byte IV")
            context = context_factory(header)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=".cryptocore-",
                suffix=".tmp", delete=False,
            ) as outgoing:
                temporary = Path(outgoing.name)
                outgoing.write(output_prefix)
                while chunk := incoming.read(chunk_size):
                    outgoing.write(context.update(chunk))
                outgoing.write(context.finalize())
                outgoing.flush()
                os.fsync(outgoing.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
