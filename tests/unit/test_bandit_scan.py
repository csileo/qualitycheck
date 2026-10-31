import json
import sys
from pathlib import Path

import pytest
from bandit.core.manager import BanditManager
from conftest import read

from qualitycheck import bandit_scan


@pytest.mark.test_cases("bandit-scan")
def test_one_scan_writes_both_reports(case, tmp_path, monkeypatch):
    input_dir, snapshot = case
    monkeypatch.setattr(BanditManager, "output_results", BanditManager.output_results)
    monkeypatch.setattr(sys, "argv", sys.argv)
    monkeypatch.chdir(input_dir)
    html, report = tmp_path / "bandit.html", tmp_path / "bandit.json"
    # A file, not stdout: bandit closes the output it writes to.
    arguments = [*read(input_dir, "arguments.txt").split(), "-o", str(report)]
    with pytest.raises(SystemExit) as stopped:
        bandit_scan.main([str(html), *arguments])
    results = json.loads(report.read_text(encoding="utf-8"))["results"]
    lines = [f"exit: {stopped.value.code}"]
    for item in results:
        place = f"{Path(item['filename']).as_posix()}:{item['line_number']}"
        in_html = item["test_id"] in html.read_text(encoding="utf-8")
        lines.append(f"{place} {item['test_id']} in html: {in_html}")
    assert "\n".join(lines) + "\n" == snapshot
