"""Internal bounded-tail buffering shared by padded block operations."""

from ..aes import AES128, BLOCK_SIZE
from ..padding import pad, unpad


class PaddedMode:
    """Incremental block processing; decryption retains its final block."""

    def __init__(self, key: bytes, encrypt: bool):
        if type(encrypt) is not bool:
            raise TypeError("encrypt must be bool")
        self._aes = AES128(key)
        self._encrypt = encrypt
        self._buffer = b""
        self._finished = False

    def _check_active(self) -> None:
        if self._finished:
            raise ValueError("Context has already been finalized")

    def _transform_block(self, block: bytes) -> bytes:
        raise NotImplementedError

    def update(self, data: bytes) -> bytes:
        """Process complete blocks while retaining only an incomplete tail."""
        self._check_active()
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        data = self._buffer + data
        blocks = len(data) // BLOCK_SIZE
        if not self._encrypt:
            blocks = max(0, blocks - 1)
        end = blocks * BLOCK_SIZE
        output = bytearray()
        for offset in range(0, end, BLOCK_SIZE):
            output.extend(self._transform_block(data[offset:offset + BLOCK_SIZE]))
        self._buffer = data[end:]
        return bytes(output)

    def finalize(self) -> bytes:
        """Apply/check PKCS#7 once; reject empty or misaligned ciphertext."""
        self._check_active()
        self._finished = True
        tail, self._buffer = self._buffer, b""
        if self._encrypt:
            return self._transform_block(pad(tail))
        if len(tail) != BLOCK_SIZE:
            raise ValueError("Ciphertext must contain complete 16-byte blocks")
        return unpad(self._transform_block(tail))
