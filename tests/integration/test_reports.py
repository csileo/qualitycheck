import pytest
from conftest import normalized


@pytest.mark.test_cases("projects")
def test_report(case, checked):
    input_dir, snapshot = case
    project, _ = checked(input_dir.parent.name)
    report = (project / "docs/qualitycheck-report/report.md").read_text(
        encoding="utf-8"
    )
    assert normalized(report, project) == snapshot
