import json

import pytest
from conftest import read

from qualitycheck.lychee import asset, broken_and_unchecked


@pytest.mark.test_cases("lychee-report")
def test_broken_and_unchecked(case):
    input_dir, snapshot = case
    report = json.loads(read(input_dir, "report.json"))
    broken, unchecked = broken_and_unchecked(report)
    lines = [f"broken: {f.path}:{f.line} {f.code} {f.message}" for f in broken]
    assert "\n".join([*lines, f"unchecked: {unchecked}"]) + "\n" == snapshot


@pytest.mark.test_cases("lychee-assets")
def test_one_pinned_asset_per_platform(case):
    input_dir, snapshot = case
    lines = []
    for platform in read(input_dir, "platforms.txt").splitlines():
        found = asset(*platform.split())
        assert found is None or len(found[1]) == 64
        lines.append(f"{platform}: {found[0] if found else 'none'}")
    assert "\n".join(lines) + "\n" == snapshot
