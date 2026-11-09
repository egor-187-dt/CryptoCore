"""Record fresh STS availability and verify a newly built wheel in isolation.

Run from the project venv. No system components are installed; the wheel test
uses a temporary venv without system site packages and runs the existing suite.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "verification"


def save(name, record):
    (EVIDENCE / name).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def probe_sts():
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "requirement": "S3-TEST-3",
        "platform": platform.platform(),
        "tool_lookup": {name: shutil.which(name) for name in
                        ("assess", "assess.exe", "gcc", "cc", "clang", "cl", "make")},
        "compiler_paths": {path: Path(path).is_file() for path in (
            "C:/msys64/ucrt64/bin/gcc.exe", "C:/msys64/mingw64/bin/gcc.exe",
            "C:/MinGW/bin/gcc.exe", "C:/Program Files/LLVM/bin/clang.exe",
            "C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")},
        "sts_run": False,
        "status": "BLOCKED",
        "p_values": None,
    }
    try:
        result = subprocess.run(["assess", "1000000"], cwd=ROOT, input=b"",
                                capture_output=True, timeout=30)
        record["attempt"] = {"command": ["assess", "1000000"],
                             "returncode": result.returncode,
                             "stdout": result.stdout.decode(errors="replace"),
                             "stderr": result.stderr.decode(errors="replace")}
    except (OSError, subprocess.TimeoutExpired) as error:
        record["attempt"] = {"command": ["assess", "1000000"],
                             "error_type": type(error).__name__,
                             "winerror": getattr(error, "winerror", None), "error": str(error)}
    if os.name == "nt":
        try:
            result = subprocess.run(["wsl", "--list", "--quiet"], capture_output=True, timeout=30)
            record["wsl"] = {"returncode": result.returncode,
                             "stdout": result.stdout.decode("utf-16-le", errors="replace").strip(),
                             "stderr": result.stderr.decode("utf-16-le", errors="replace").strip()}
        except (OSError, subprocess.TimeoutExpired) as error:
            record["wsl"] = {"error": str(error)}
    sample = ROOT / "artifacts/nist/random.bin"
    baseline = json.loads((EVIDENCE / "nist_data.json").read_text(encoding="utf-8"))
    record["existing_sample"] = {"exists": sample.is_file()}
    if sample.is_file():
        record["existing_sample"].update(
            bytes=sample.stat().st_size, sha256=hashlib.sha256(sample.read_bytes()).hexdigest())
        record["existing_sample"]["matches_saved_metadata"] = (
            record["existing_sample"]["sha256"] == baseline["sha256"]
            and sample.stat().st_size == baseline["bytes"])
    record["reason"] = (
        "No official STS results: assess invocation and tool availability are recorded; "
        "all 15 tests and their p-values remain unverified."
    )
    external = EVIDENCE / "nist_sts_results.json"
    if external.is_file():
        evidence = json.loads(external.read_text(encoding="utf-8"))
        if evidence.get("status") == "PASSED" and evidence.get("official_sts_executed"):
            record.update(status="PASSED", verified_external_run="verification/nist_sts_results.json",
                          reason="Official STS run recorded; regression validates raw reports and provenance. "
                                 "This availability probe itself does not rerun STS.")
    save("stage1_nist_recheck.json", record)
    print("Fresh STS availability evidence recorded", flush=True)


def verify_wheel():
    record = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "commands": [], "status": "FAILED"}
    log = []

    def run(args, cwd=ROOT, accepted=(0,)):
        args = [str(arg) for arg in args]
        print("Running " + " ".join(args[:5]), flush=True)
        result = subprocess.run(args, cwd=cwd, capture_output=True, encoding="utf-8",
                                errors="replace", timeout=900)
        record["commands"].append({"argv": args, "cwd": str(cwd),
                                   "returncode": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr})
        log.append(f"COMMAND: {args!r}\nCWD: {cwd}\nEXIT: {result.returncode}\n"
                   + result.stdout + result.stderr)
        if result.returncode not in accepted:
            raise RuntimeError(f"Command failed with exit {result.returncode}: {args[:5]}")
        return result

    try:
        wheels = ROOT / "artifacts/stage1_audit/wheels"
        wheels.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "pip", "check"])
        run([sys.executable, "-m", "pip", "wheel", "--no-build-isolation", "--no-deps",
             ROOT, "--wheel-dir", wheels])
        run([sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--no-deps",
             "pycryptodome==4.3.0", "--dest", wheels])
        wheel = wheels / "cryptocore-0.1.0-py3-none-any.whl"
        record["wheel"] = wheel.relative_to(ROOT).as_posix()
        record["wheel_sha256"] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="CryptoCore wheel audit ") as folder:
            isolated = Path(folder)
            venv.EnvBuilder(with_pip=True, system_site_packages=False).create(isolated / "venv")
            scripts = isolated / "venv" / ("Scripts" if os.name == "nt" else "bin")
            python = scripts / ("python.exe" if os.name == "nt" else "python")
            cli = scripts / ("cryptocore.exe" if os.name == "nt" else "cryptocore")
            run([python, "-m", "pip", "install", "--no-index", "--find-links", wheels,
                 wheel], cwd=isolated)
            run([python, "-m", "pip", "check"], cwd=isolated)
            result = run([python, "-I", "-c",
                          "import cryptocore, json, sys; from pathlib import Path; "
                          "p=Path(cryptocore.__file__).resolve(); "
                          "assert p.is_relative_to(Path(sys.prefix).resolve()); "
                          "assert 'site-packages' in p.parts; "
                          "print(json.dumps({'module': str(p), 'prefix': sys.prefix}))"], cwd=isolated)
            record["isolated_import"] = json.loads(result.stdout)
            run([cli, "--help"], cwd=isolated)
            run([python, ROOT / "tools/prepare_nist_data.py",
                 "--output", ROOT / "artifacts/stage1_audit/random.bin",
                 "--metadata", EVIDENCE / "stage1_nist_data.json"], cwd=isolated)
            result = run([python, ROOT / "tests/run_tests.py", "--report",
                          EVIDENCE / "stage1_wheel_tests.json"], cwd=isolated, accepted=(0, 2))
            tests = json.loads((EVIDENCE / "stage1_wheel_tests.json").read_text(encoding="utf-8"))
            assert tests["failures"] == tests["errors"] == 0
            assert tests["skipped"] in (0, 1), tests["skipped_details"]
            if tests["skipped"]:
                assert tests["skipped_details"][0][0].endswith("test_official_nist_sts_all_15")
            record["wheel_suite"] = {key: tests[key] for key in
                                     ("tests_run", "passed", "failures", "errors", "skipped")}
            record["status"] = "PASSED"
            record["stage1_complete"] = not tests["skipped"]
            record["note"] = ("Wheel installation and regression passed; official STS evidence verified."
                              if record["stage1_complete"] else
                              "Wheel installation and regression passed; official NIST STS remains BLOCKED.")
    finally:
        record["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save("stage1_packaging_recheck.json", record)
        (EVIDENCE / "stage1_packaging_recheck.log").write_text("\n".join(log), encoding="utf-8")
    print("Wheel verification complete; see verification/stage1_packaging_recheck.json", flush=True)


if __name__ == "__main__":
    probe_sts()
    verify_wheel()
