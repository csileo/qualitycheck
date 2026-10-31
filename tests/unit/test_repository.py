import pytest
from conftest import read

from qualitycheck.repository import not_done


@pytest.mark.test_cases("git-failure")
def test_not_done(case):
    input_dir, snapshot = case
    assert (
        not_done("the report was not pushed", read(input_dir, "stderr.txt")) + "\n"
        == snapshot
    )
