import json

import pytest
from conftest import measures_from, read

from qualitycheck.gates import evaluate, result


@pytest.mark.test_cases("gates")
def test_gates(case):
    input_dir, snapshot = case
    data = json.loads(read(input_dir, "measures.json"))
    gates = evaluate(measures_from(data), data.get("fail_under", 80))
    lines = [f"{gate.name}: {gate.status} - {gate.detail}" for gate in gates]
    assert "\n".join([*lines, f"result: {result(gates)}"]) + "\n" == snapshot
