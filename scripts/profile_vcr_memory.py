#!/usr/bin/env python3
"""
Local memory profiler for keboola.vcr recording.

Usage (no installation needed — resolves keboola.vcr from sibling repo):
    python scripts/profile_vcr_memory.py

Or install keboola.vcr first and then run normally:
    pip install -e /path/to/python-vcr-tests
    python scripts/profile_vcr_memory.py

Outputs peak RSS and tracemalloc peak for a VCR-recorded run so memory
overhead is immediately visible.
"""
import json
import os
import resource
import shutil
import sys
import tempfile
import tracemalloc
from pathlib import Path

# Resolve keboola.vcr from the sibling python-vcr-tests repo when it is not
# installed in the active environment (common in local dev).
_here = Path(__file__).resolve().parent          # .../component-ceps/scripts
_vcr_src = _here.parent.parent / "python-vcr-tests" / "src"
if _vcr_src.exists():
    sys.path.insert(0, str(_vcr_src))

from keboola.vcr import VCRRecorder

# ---- large config for stress-testing ----------------------------------------
LARGE_CONFIG = {
    "parameters": {
        "date_from": "2020-01-01",
        "date_to": "2021-01-01",  # 1 year of quarter-hourly data
        "continue_on_fail": True,
        "endpoints": [
            {"endpoint_name": "CrossborderPowerFlows", "granularity": "QH"},
            {"endpoint_name": "Generation", "granularity": "QH"},
            {"endpoint_name": "Load", "granularity": "QH"},
            {"endpoint_name": "GenerationRES", "granularity": "QH"},
        ],
    }
}
# -----------------------------------------------------------------------------


def make_runner(data_dir: str):
    """Return a zero-arg callable that runs the component once."""
    _src = str(Path(__file__).parent.parent / "src")

    def _run():
        os.environ["KBC_DATADIR"] = data_dir
        if _src not in sys.path:
            sys.path.insert(0, _src)
        from component import Component  # noqa — local component module

        comp = Component()
        comp.execute_action()

    return _run


def peak_rss_mb() -> float:
    # Both macOS and Linux return bytes
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / (1024 * 1024)


def run_with_profiling(label: str, fn):
    tracemalloc.start()
    fn()
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss = peak_rss_mb()
    print(f"[{label}]  tracemalloc peak: {peak / 1e6:.1f} MB   RSS peak: {rss:.1f} MB")


def main():
    tmp = tempfile.mkdtemp(prefix="ceps_vcr_test_")
    try:
        os.makedirs(f"{tmp}/out/tables", exist_ok=True)
        with open(f"{tmp}/config.json", "w") as f:
            json.dump(LARGE_CONFIG, f)

        cassette_dir = Path(tmp) / "cassettes"
        recorder = VCRRecorder(cassette_dir=cassette_dir)
        runner = make_runner(tmp)

        run_with_profiling("VCR record", lambda: recorder.record(runner))

        cassette_path = cassette_dir / "requests.json"
        print(f"\nCassette: {cassette_path}")
        if cassette_path.exists():
            cass_size = cassette_path.stat().st_size / 1e6
            print(f"Cassette size: {cass_size:.1f} MB")
        else:
            print("Cassette not written (component may have made no HTTP requests)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
