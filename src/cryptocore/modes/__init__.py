"""Student implementations of block cipher modes."""

from .ecb import ECB
from .cbc import CBC
from .cfb import CFB
from .ofb import OFB
from .ctr import CTR

MODE_NAMES = ("ecb", "cbc", "cfb", "ofb", "ctr")


def create_context(mode: str, key: bytes, encrypt: bool, iv: bytes | None = None):
    """Build a new single-use streaming operation context."""
    if mode == "ecb":
        if iv is not None:
            raise ValueError("ECB does not use an IV")
        return ECB(key, encrypt)
    implementations = {"cbc": CBC, "cfb": CFB, "ofb": OFB, "ctr": CTR}
    if mode not in implementations:
        raise ValueError("Unsupported mode")
    return implementations[mode](key, iv, encrypt)
