"""Strict AES-128 single-block adapter; no file or mode processing here."""

from Crypto.Cipher import AES

BLOCK_SIZE = 16


class AES128:
    """Reuse a library AES schedule, exposing only 16-byte block operations."""

    def __init__(self, key: bytes):
        if not isinstance(key, bytes) or len(key) != BLOCK_SIZE:
            raise ValueError("AES-128 key must contain exactly 16 bytes")
        self._cipher = AES.new(key, AES.MODE_ECB)

    @staticmethod
    def _validate(block: bytes) -> None:
        if not isinstance(block, bytes) or len(block) != BLOCK_SIZE:
            raise ValueError("AES block must contain exactly 16 bytes")

    def encrypt_block(self, block: bytes) -> bytes:
        """Encrypt exactly one block."""
        self._validate(block)
        return self._cipher.encrypt(block)

    def decrypt_block(self, block: bytes) -> bytes:
        """Decrypt exactly one block."""
        self._validate(block)
        return self._cipher.decrypt(block)


def encrypt_block(key: bytes, block: bytes) -> bytes:
    """Encrypt one block with a 16-byte key; invalid lengths raise ValueError."""
    return AES128(key).encrypt_block(block)


def decrypt_block(key: bytes, block: bytes) -> bytes:
    """Decrypt one block with a 16-byte key; invalid lengths raise ValueError."""
    return AES128(key).decrypt_block(block)
