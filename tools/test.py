"""Run ordinary regressions, optionally followed by the full gameplay matrix.

Plain unittest discovery remains supported. This runner moves exactly one
expensive test to the existing parallel matrix runner; every other discovered
test, including discovery/import failures, remains in the regression suite.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
for source_root in (ROOT, ROOT / "src"):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
EXHAUSTIVE_TEST = "test_world.WorldTests.test_all_component_mixes_update_and_fire_safely"


def iter_tests(suite):
    """Yield leaf test cases without changing their order or swallowing errors."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def regression_suite(discovered):
    """Split the one known matrix test out, rejecting missing/duplicate matches."""
    tests = list(iter_tests(discovered))
    excluded = [test.id() for test in tests if test.id() == EXHAUSTIVE_TEST]
    if excluded != [EXHAUSTIVE_TEST]:
        raise ValueError(f"Expected exactly one exhaustive test {EXHAUSTIVE_TEST!r}; found {len(excluded)}")
    selected = [test for test in tests if test.id() != EXHAUSTIVE_TEST]
    if not selected:
        raise ValueError("Refusing to run an empty regression suite")
    return unittest.TestSuite(selected), excluded


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Also run the exhaustive matrix in independent processes")
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=4, help="Matrix worker count (default: 4)")
    parser.add_argument("--output", type=Path, default=ROOT / "output/tests", help="Directory for regression and matrix reports")
    parser.add_argument("--list", action="store_true", help="List selected regression IDs without running them")
    args = parser.parse_args(argv)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    discovered = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    try:
        suite, excluded = regression_suite(discovered)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    count = suite.countTestCases()
    print(f"Selected {count} regression tests; excluded exactly: {excluded[0]}", flush=True)
    print("The excluded assertions run through tools/verify_matrix.py" + (" after regressions." if args.full else " with --full."), flush=True)
    if args.list:
        for test in iter_tests(suite):
            print(test.id())
        return 0

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "tests_selected": count,
        "tests_run": result.testsRun,
        "excluded": excluded,
        "failures": [test.id() for test, _ in result.failures],
        "errors": [test.id() for test, _ in result.errors],
        "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
        "unexpected_successes": [test.id() for test in result.unexpectedSuccesses],
        "seconds": round(time.perf_counter() - start, 3),
        "passed": result.wasSuccessful() and result.testsRun == count,
        "matrix_requested": args.full,
        "matrix_exit_code": None,
    }
    report_path = output / "regressions.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        return 1
    if args.full:
        completed = subprocess.run([
            sys.executable, "-u", str(ROOT / "tools/verify_matrix.py"),
            "--workers", str(args.workers), "--output", str(output / "matrix.json"),
        ], cwd=ROOT)
        report["matrix_exit_code"] = completed.returncode
        report["passed"] = completed.returncode == 0
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return int(not report["passed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
