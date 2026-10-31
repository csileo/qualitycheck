import json

import pytest
from conftest import read

from qualitycheck.history import append, last_pass, parse


@pytest.mark.test_cases("history")
def test_history(case):
    input_dir, snapshot = case
    row = json.loads(read(input_dir, "row.json"))
    text = append(read(input_dir, "previous.csv"), row)
    passed = last_pass(parse(text))
    assert text + f"last pass: {passed['commit'] if passed else 'none'}\n" == snapshot
