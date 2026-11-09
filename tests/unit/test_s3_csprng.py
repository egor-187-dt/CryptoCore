"""OS RNG, uniqueness, Hamming weight and failure handling; not NIST STS."""

import inspect
import unittest
from unittest.mock import patch

from cryptocore import csprng
from tests.support import METRICS


class CSPRNGTests(unittest.TestCase):
    def test_signature_and_lengths(self):
        self.assertEqual(list(inspect.signature(csprng.generate_random_bytes).parameters), ["num_bytes"])
        for length in (0, 1, 16, 17, 4096, 65536):
            result = csprng.generate_random_bytes(length)
            self.assertIsInstance(result, bytes)
            self.assertEqual(len(result), length)

    def test_uses_os_urandom(self):
        with patch("cryptocore.csprng.os.urandom", return_value=b"x"*16) as source:
            self.assertEqual(csprng.generate_random_bytes(16), b"x"*16)
            source.assert_called_once_with(16)

    def test_invalid_counts(self):
        for count in (True, False, "16", None, 1.5):
            with self.assertRaises(TypeError):
                csprng.generate_random_bytes(count)
        with self.assertRaises(ValueError):
            csprng.generate_random_bytes(-1)

    def test_os_failures_and_malformed_results(self):
        for failure in (OSError("injected OS failure"), OverflowError("count too large")):
            with patch("cryptocore.csprng.os.urandom", side_effect=failure):
                with self.assertRaisesRegex(OSError, "CSPRNG"):
                    csprng.generate_random_bytes(16)
        for result in (None, b"", bytes(15), bytes(17), "x"*16):
            with patch("cryptocore.csprng.os.urandom", return_value=result):
                with self.assertRaisesRegex(OSError, "CSPRNG"):
                    csprng.generate_random_bytes(16)

    def test_1000_unique_keys(self):
        keys = [csprng.generate_random_bytes(16) for _ in range(1000)]
        self.assertEqual(len(set(keys)), 1000)
        METRICS["unique_keys_of_1000"] = len(set(keys))

    def test_basic_hamming_distribution(self):
        sample = b"".join(csprng.generate_random_bytes(16) for _ in range(1000))
        proportion = sum(byte.bit_count() for byte in sample) / (len(sample)*8)
        # Broad smoke bound, not evidence of cryptographic strength or STS success.
        self.assertGreater(proportion, 0.48)
        self.assertLess(proportion, 0.52)
        METRICS["hamming_one_proportion_128000bits"] = proportion
