"""CTR: full 128-bit big-endian counter initialized from IV, no wraparound."""

from ._stream import StreamMode


class CTR(StreamMode):
    """Increment after each block; exhausting the counter raises ValueError."""

    def __init__(self, key: bytes, iv: bytes, encrypt: bool):
        super().__init__(key, iv, encrypt)
        self._counter = int.from_bytes(iv, "big")

    def _next_gamma(self) -> bytes:
        if self._counter >= 1 << 128:
            raise ValueError("CTR counter exhausted; refusing to reuse keystream")
        gamma = self._aes.encrypt_block(self._counter.to_bytes(16, "big"))
        self._counter += 1
        return gamma
