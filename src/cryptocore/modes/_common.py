"""Small mode helpers: fixed-size IV validation and XOR."""


def validate_iv(iv: bytes) -> bytes:
    """Reject missing, nonbinary or non-16-byte initialization vectors."""
    if not isinstance(iv, bytes) or len(iv) != 16:
        raise ValueError("IV must contain exactly 16 bytes")
    return iv


def xor_bytes(left: bytes, right: bytes) -> bytes:
    """XOR equally sized slices, rejecting accidental truncation."""
    if len(left) != len(right):
        raise ValueError("XOR operands must have equal length")
    return bytes(a ^ b for a, b in zip(left, right))
