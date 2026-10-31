import pytest
from conftest import read

from qualitycheck.tools import missing_module


@pytest.mark.test_cases("missing-module")
def test_missing_module(case):
    input_dir, snapshot = case
    module = read(input_dir, "module.txt").strip()
    found = missing_module(module, read(input_dir, "stderr.txt"))
    assert f"missing: {found}\n" == snapshot
