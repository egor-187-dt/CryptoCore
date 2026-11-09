"""Common chunk-independent buffering for full-block keystream modes."""

from ..aes import AES128
from ._common import validate_iv, xor_bytes


class StreamMode:
    """Retain unused keystream bytes across updates, without adding padding."""

    def __init__(self, key: bytes, iv: bytes, encrypt: bool):
        if type(encrypt) is not bool:
            raise TypeError("encrypt must be bool")
        self._aes = AES128(key)
        self._register = validate_iv(iv)
        self._encrypt = encrypt
        self._position = 16
        self._gamma = b""
        self._finished = False

    def _next_gamma(self) -> bytes:
        raise NotImplementedError

    def _feedback(self, incoming: bytes, outgoing: bytes) -> None:
        """Only feedback modes override this hook."""

    def _check_active(self) -> None:
        if self._finished:
            raise ValueError("Context has already been finalized")

    def update(self, data: bytes) -> bytes:
        """Process any byte length while respecting 128-bit segment boundaries."""
        self._check_active()
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        output = bytearray()
        offset = 0
        while offset < len(data):
            if self._position == 16:
                self._gamma = self._next_gamma()
                self._position = 0
            count = min(16 - self._position, len(data) - offset)
            incoming = data[offset:offset + count]
            result = xor_bytes(incoming, self._gamma[self._position:self._position + count])
            self._feedback(incoming, result)
            output.extend(result)
            self._position += count
            offset += count
        return bytes(output)

    def finalize(self) -> bytes:
        """Finish once; no padding or additional ciphertext is produced."""
        self._check_active()
        self._finished = True
        self._gamma = b""
        return b""
