"""Student CBC chaining over the AES block adapter, with PKCS#7."""

from ._common import validate_iv, xor_bytes
from ._padded import PaddedMode


class CBC(PaddedMode):
    """Streaming CBC with one-block chaining state."""

    def __init__(self, key: bytes, iv: bytes, encrypt: bool):
        super().__init__(key, encrypt)
        self._previous = validate_iv(iv)

    def _transform_block(self, block: bytes) -> bytes:
        if self._encrypt:
            result = self._aes.encrypt_block(xor_bytes(block, self._previous))
            self._previous = result
        else:
            result = xor_bytes(self._aes.decrypt_block(block), self._previous)
            self._previous = block
        return result
