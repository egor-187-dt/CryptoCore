"""Generated-key CLI contract and shared key/IV randomness."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from cryptocore.cli import main
from cryptocore.modes import create_context
from tests.support import KEY, ROOT, METRICS, command, crypt, run_cli


class GeneratedKeyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="CryptoCore key кириллица ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source, self.cipher, self.restored = [self.root/name for name in ("данные p", "данные c", "данные r")]
        self.source.write_bytes(bytes(range(256)) + b"tail\x00\xff")

    def auto_command(self, mode):
        args = command(mode, True, self.source, self.cipher)
        del args[args.index("--key"):args.index("--key")+2]
        return args

    def test_generated_key_roundtrip_all_modes(self):
        for mode in ("ecb", "cbc", "cfb", "ofb", "ctr"):
            result = run_cli(*self.auto_command(mode))
            self.assertEqual(result.returncode, 0, result.stderr)
            match = re.fullmatch(rb"\[INFO\] Generated random key: ([0-9a-f]{32})\r?\n", result.stdout)
            self.assertIsNotNone(match)
            key = bytes.fromhex(match[1].decode())
            result = run_cli(*command(mode, False, self.cipher, self.restored, key))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.restored.read_bytes(), self.source.read_bytes())

    def test_decryption_requires_key_all_modes(self):
        for mode in ("ecb", "cbc", "cfb", "ofb", "ctr"):
            args = self.auto_command(mode)
            args[args.index("--encrypt")] = "--decrypt"
            result = run_cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"--key", result.stderr)
            self.assertEqual(result.stdout, b"")

    def test_key_printed_immediately_once_and_never_serialized(self):
        iv = bytes(range(16))
        key = bytes.fromhex("112233445566778899aabbccddeeff00")
        for mode in ("ecb", "cbc", "cfb", "ofb", "ctr"):
            calls = 0
            with redirect_stdout(io.StringIO()) as output:
                def rng(count):
                    nonlocal calls
                    self.assertEqual(count, 16)
                    if calls:
                        self.assertEqual(output.getvalue(), f"[INFO] Generated random key: {key.hex()}\n")
                    calls += 1
                    return key if calls == 1 else iv
                with patch("cryptocore.cli.csprng.generate_random_bytes", side_effect=rng):
                    self.assertEqual(main(self.auto_command(mode)), 0)
            self.assertEqual(calls, 1 if mode == "ecb" else 2)
            self.assertEqual(output.getvalue(), f"[INFO] Generated random key: {key.hex()}\n")
            expected = crypt(create_context(mode, key, True, None if mode == "ecb" else iv), self.source.read_bytes(), 7)
            # Exact equality to IV||C (or C) proves no key field was added.
            self.assertEqual(self.cipher.read_bytes(), (b"" if mode == "ecb" else iv) + expected)

    def test_rng_failures_preserve_output_and_limit_key_output(self):
        self.cipher.write_bytes(b"KEEP")
        for values, expected_lines in (([OSError("key RNG failure")], 0), ([KEY, OSError("IV RNG failure")], 1)):
            with patch("cryptocore.cli.csprng.generate_random_bytes", side_effect=values):
                with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(main(self.auto_command("cbc")), 1)
            self.assertEqual(output.getvalue().count("Generated random key:"), expected_lines)
            self.assertIn("RNG", errors.getvalue())
            self.assertEqual(self.cipher.read_bytes(), b"KEEP")
            self.assertEqual(list(self.root.glob(".cryptocore-*.tmp")), [])

    def test_supplied_key_unchanged_and_weak_warning(self):
        for key in (bytes(16), bytes(range(16)), bytes(range(15,-1,-1)), KEY):
            with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
                with patch("cryptocore.cli.csprng.generate_random_bytes") as rng:
                    self.assertEqual(main(command("ecb", True, self.source, self.cipher, key)), 0)
                    rng.assert_not_called()
            self.assertEqual(output.getvalue(), "")
            self.assertEqual("warning" in errors.getvalue(), key != KEY)
            self.assertEqual(self.cipher.read_bytes(), crypt(create_context("ecb", key, True), self.source.read_bytes(), 7))

    def test_1000_ivs_from_shared_generator(self):
        from cryptocore.csprng import generate_random_bytes
        self.source.write_bytes(b"")
        seen = set()
        with patch("cryptocore.cli.csprng.generate_random_bytes", wraps=generate_random_bytes) as rng:
            for index in range(1000):
                mode = ("cbc", "cfb", "ofb", "ctr")[index % 4]
                self.assertEqual(main(command(mode, True, self.source, self.cipher)), 0)
                seen.add(self.cipher.read_bytes()[:16])
            self.assertEqual(rng.call_count, 1000)
        self.assertEqual(len(seen), 1000)
        METRICS["unique_ivs_of_1000"] = len(seen)


class NISTSTSAvailabilityTests(unittest.TestCase):
    def test_official_nist_sts_all_15(self):
        # Validate the actual external run, including raw output and provenance.
        # This regression does not rerun STS or replace it with a Python test.
        import hashlib
        import math
        import re
        import zipfile

        path = ROOT / "verification/nist_sts_results.json"
        if not path.is_file():
            self.skipTest("Official NIST STS evidence unavailable; see TESTING.md")
        evidence = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["requirement"], "S3-TEST-3")
        if evidence["status"] in ("BLOCKED", "NOT_VERIFIED"):
            self.skipTest(evidence.get("reason", "Official STS not verified"))
        self.assertEqual(evidence["status"], "PASSED")
        self.assertTrue(evidence["official_sts_executed"])
        self.assertEqual(evidence["tests_executed"], 15)
        self.assertEqual(evidence["sequences_tested"], 800)
        self.assertEqual(evidence["subtests_evaluated"], 188)
        self.assertGreaterEqual(evidence["families_strictly_passed"], 8)
        self.assertTrue(evidence["contiguous_batches_cover_sample_exactly"])
        self.assertTrue(evidence["sleep_guard_enabled_and_cleared"])

        def digest(relative):
            return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()

        self.assertEqual(digest("src/cryptocore/csprng.py"), evidence["csprng_source_sha256"])
        self.assertEqual(digest("verification/nist_sts_protocol.json"), evidence["protocol_sha256"])
        sample = evidence["sample"]
        self.assertEqual((ROOT / sample["path"]).stat().st_size, 100000000)
        self.assertEqual(digest(sample["path"]), sample["sha256"])
        self.assertEqual(digest(evidence["raw_archive"]), evidence["raw_archive_sha256"])
        source = json.loads((ROOT / "verification/nist_sts_source.json").read_text())
        self.assertEqual(digest(source["file"]), evidence["source_archive_sha256"])
        build = json.loads((ROOT / "verification/nist_sts_build.json").read_text())
        self.assertEqual(digest(build["executable"]), evidence["executable_sha256"])
        protocol = json.loads((ROOT / "verification/nist_sts_protocol.json").read_text())
        self.assertEqual([t["id"] for t in evidence["tests"]], list(range(1, 16)))

        with zipfile.ZipFile(ROOT / evidence["raw_archive"]) as archive:
            self.assertIsNone(archive.testzip())
            frequency = archive.read("combined/experiments/AlgorithmTesting/freq.txt").decode()
            self.assertEqual(len(re.findall(r"BITSREAD = 1000000", frequency)), 800)
            for actual, expected in zip(evidence["tests"], protocol["tests"]):
                with self.subTest(test=actual["name"]):
                    self.assertEqual(actual["parameters"], expected["parameters"])
                    self.assertEqual(actual["execution_status"], "COMPLETED")
                    self.assertEqual(actual["sequences_attempted"], 800)
                    self.assertGreaterEqual(actual["sequences_applicable"], 55)
                    base = "combined/experiments/AlgorithmTesting/" + actual["directory"] + "/"
                    values = list(map(float, archive.read(base + "results.txt").split()))
                    self.assertEqual(len(values), 800 * expected["subtests"])
                    self.assertTrue(all(math.isfinite(p) and 0 <= p <= 1 for p in values))
                    mask = [True] * 800
                    if actual["id"] in (12, 13):
                        stats = archive.read(base + "stats.txt").decode()
                        cycles = list(map(int, re.findall(r"Number Of Cycles \(J\)\s*=\s*(\d+)", stats)))
                        self.assertEqual(len(cycles), 800)
                        mask = [count >= 500 for count in cycles]
                    self.assertEqual(mask, actual["applicable_mask"])
                    self.assertEqual(sum(mask), actual["sequences_applicable"])
                    self.assertEqual(len(actual["series"]), expected["subtests"])
                    for index, series in enumerate(actual["series"]):
                        raw = values[index::expected["subtests"]]
                        self.assertEqual(series["p_values"], [p if ok else None for p, ok in zip(raw, mask)])
                        eligible = [p for p, ok in zip(raw, mask) if ok]
                        self.assertEqual(series["passed"], sum(p >= 0.01 for p in eligible))
                        self.assertEqual(series["applicable"], len(eligible))
