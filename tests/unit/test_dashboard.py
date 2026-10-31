import json

import pytest
from conftest import measures_from, read

from qualitycheck import dashboard
from qualitycheck.gates import evaluate
from qualitycheck.history import parse
from qualitycheck.report import Run


@pytest.mark.test_cases("dashboard")
def test_dashboard(case):
    input_dir, snapshot = case
    data = json.loads(read(input_dir, "measures.json"))
    fail_under = data.get("fail_under", 80)
    measures = measures_from(data)
    run = Run(**json.loads(read(input_dir, "run.json")))
    rows = parse(read(input_dir, "history.csv"))
    images = dashboard.images(
        run, evaluate(measures, fail_under), measures, rows, fail_under
    )
    parts = ["\n".join(dashboard.markdown(images)) + "\n"]
    parts += [f"=== {image.name}.svg\n{image.svg}" for image in images]
    assert "\n".join(parts) == snapshot
