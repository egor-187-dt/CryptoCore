"""PKCS#7 padding implemented independently of cryptographic libraries."""


def _validate_size(block_size: int) -> None:
    if type(block_size) is not int or not 1 <= block_size <= 255:
        raise ValueError("PKCS#7 block size must be an integer in 1..255")


def pad(data: bytes, block_size: int = 16) -> bytes:
    """Append PKCS#7, including a full block for aligned or empty input."""
    _validate_size(block_size)
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    count = block_size - len(data) % block_size
    return data + bytes([count]) * count


def unpad(data: bytes, block_size: int = 16) -> bytes:
    """Check length and every padding byte; malformed padding raises ValueError."""
    _validate_size(block_size)
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not data or len(data) % block_size:
        raise ValueError("Invalid PKCS#7 padded length")
    count = data[-1]
    if not 1 <= count <= block_size or data[-count:] != bytes([count]) * count:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-count]
