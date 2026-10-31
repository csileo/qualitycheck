import datetime as dt
import json

import pytest
from conftest import read

from qualitycheck.history import parse
from qualitycheck.status import reminder


@pytest.mark.test_cases("reminder")
def test_reminder(case):
    input_dir, snapshot = case
    context = json.loads(read(input_dir, "context.json"))
    warning = reminder(
        parse(read(input_dir, "history.csv")),
        context["commits_since"],
        dt.datetime.fromisoformat(context["now"]),
        (context["max_commits"], context["max_days"]),
    )
    assert f"{warning or 'none'}\n" == snapshot
