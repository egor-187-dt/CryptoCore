"""OFB: plaintext-independent AES feedback generates a byte stream."""

from ._stream import StreamMode


class OFB(StreamMode):
    """Encrypt the previous keystream block, starting with the supplied IV."""

    def _next_gamma(self) -> bytes:
        self._register = self._aes.encrypt_block(self._register)
        return self._register
