"""Run all tests in one command and optionally persist factual JSON evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.support import METRICS, openssl_path


class Tee:
    """Stream progress immediately while retaining an exact UTF-8 report log."""

    def __init__(self, log):
        self.log = log

    def write(self, text):
        self.log.write(text)
        sys.stdout.write(text)

    def flush(self):
        sys.stdout.flush()


class RecordedResult(unittest.TextTestResult):
    """Retain successful test IDs as well as failures and skips."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed_ids = []

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, help="Write JSON plus adjacent .log")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    log = io.StringIO()
    runner = unittest.TextTestRunner(stream=Tee(log), verbosity=2, resultclass=RecordedResult)
    result = runner.run(suite)
    content = log.getvalue()
    openssl = openssl_path()
    version = subprocess.run([openssl, "version"], capture_output=True, text=True, timeout=15).stdout.strip() if openssl else None
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "pycryptodome": importlib.metadata.version("pycryptodome"),
        "openssl_executable": openssl, "openssl_version": version,
        "tests_run": result.testsRun, "passed": len(result.passed_ids),
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "passed_ids": result.passed_ids,
        "complete": result.wasSuccessful() and not result.skipped,
        "metrics": METRICS,
        "failed_details": [(test.id(), reason) for test, reason in result.failures + result.errors],
        "skipped_details": [(test.id(), reason) for test, reason in result.skipped],
        "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                          for base in ("src", "tests", "tools", "requirements") for path in sorted((ROOT / base).rglob("*"))
                          if path.is_file() and "__pycache__" not in path.parts},
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.report.with_suffix(".log").write_text(content, encoding="utf-8")
    if not result.wasSuccessful():
        return 1
    if result.skipped:
        print("INCOMPLETE: external required checks were skipped; see TESTING.md")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
