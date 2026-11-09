"""Cryptographic randomness from the OS; no fallback PRNG is allowed."""

import os


def generate_random_bytes(num_bytes: int) -> bytes:
    """Return exactly num_bytes OS-random bytes.

    Noninteger counts raise TypeError, negatives raise ValueError, and an OS
    failure or malformed source result raises OSError with useful context.
    """
    if type(num_bytes) is not int:
        raise TypeError("num_bytes must be an integer")
    if num_bytes < 0:
        raise ValueError("num_bytes must be nonnegative")
    try:
        data = os.urandom(num_bytes)
    except (OSError, OverflowError) as error:
        raise OSError("CSPRNG could not obtain random bytes from the OS") from error
    if not isinstance(data, bytes) or len(data) != num_bytes:
        raise OSError("CSPRNG returned an invalid number or type of random bytes")
    return data
