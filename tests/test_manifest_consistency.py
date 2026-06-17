"""Guard against CSV/manifest column drift.

The component builds the output manifest from the static ``endpoint_columns.json`` list, while
``CachedOrthogonalDictWriter`` extends the CSV with any extra columns the API returns. If the API adds
or renames a column that is not in the static list, the CSV gains a column the manifest does not declare.
Snowflake then rejects the load with "Number of columns in file (N) does not match that of the
corresponding table (M)". The functional tests only diff the CSV against the expected CSV, so they never
catch this mismatch. This test asserts that every expected table's CSV header matches its manifest schema.
"""

import csv
import json
from pathlib import Path

import pytest

FUNCTIONAL_DIR = Path(__file__).parent / "functional"
EXPECTED_TABLES = sorted(FUNCTIONAL_DIR.glob("*/expected/data/out/tables/*.csv"))


def _case_name(csv_path: Path) -> str:
    return csv_path.relative_to(FUNCTIONAL_DIR).parts[0]


@pytest.mark.parametrize("csv_path", EXPECTED_TABLES, ids=lambda p: f"{_case_name(p)}/{p.name}")
def test_csv_columns_match_manifest(csv_path: Path):
    manifest_path = csv_path.with_suffix(csv_path.suffix + ".manifest")
    assert manifest_path.exists(), f"missing manifest for {csv_path}"

    with csv_path.open(newline="") as f:
        header = next(csv.reader(f))

    schema = json.loads(manifest_path.read_text())["schema"]
    manifest_columns = [column["name"] for column in schema]

    assert header == manifest_columns, (
        f"{_case_name(csv_path)}: CSV header {header} does not match manifest columns {manifest_columns} "
        f"(column count {len(header)} vs {len(manifest_columns)})"
    )
