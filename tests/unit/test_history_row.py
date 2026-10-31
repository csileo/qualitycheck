import json

import pytest
from conftest import measures_from, read

from qualitycheck.gates import evaluate
from qualitycheck.report import Run, history_row


@pytest.mark.test_cases("history-row")
def test_history_row(case):
    input_dir, snapshot = case
    measures = measures_from(json.loads(read(input_dir, "measures.json")))
    run = Run(**json.loads(read(input_dir, "run.json")))
    row = history_row(run, measures, evaluate(measures, 80))
    assert "".join(f"{key}: {value}\n" for key, value in row.items()) == snapshot
