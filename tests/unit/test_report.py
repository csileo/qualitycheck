import json

import pytest
from conftest import measures_from, read

from qualitycheck.gates import evaluate
from qualitycheck.history import parse
from qualitycheck.report import Run, render


@pytest.mark.test_cases("report")
def test_report(case):
    input_dir, snapshot = case
    measures = measures_from(json.loads(read(input_dir, "measures.json")))
    run = Run(**json.loads(read(input_dir, "run.json")))
    rows = parse(read(input_dir, "history.csv"))
    assert render(run, evaluate(measures, 80), measures, rows) == snapshot
