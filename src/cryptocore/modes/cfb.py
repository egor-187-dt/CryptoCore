"""CFB-128 with full ciphertext feedback, including partial final segments."""

from ._stream import StreamMode


class CFB(StreamMode):
    """AES encryption is used in both directions; feedback is ciphertext."""

    def _next_gamma(self) -> bytes:
        gamma = self._aes.encrypt_block(self._register)
        self._register = b""
        return gamma

    def _feedback(self, incoming: bytes, outgoing: bytes) -> None:
        self._register += outgoing if self._encrypt else incoming
