"""Student ECB: each block is processed independently, with PKCS#7."""

from ._padded import PaddedMode


class ECB(PaddedMode):
    """Streaming ECB encryption/decryption, not a full-file library call."""

    def _transform_block(self, block: bytes) -> bytes:
        if self._encrypt:
            return self._aes.encrypt_block(block)
        return self._aes.decrypt_block(block)
