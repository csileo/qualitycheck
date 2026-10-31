"""Run bandit's command line once, writing bandit.html besides its own output.

Bandit writes one format per scan; scanning twice doubles its time. Its own
command line runs here, so the project's settings apply as usual, and the
report step renders the same results in HTML too.

Usage: python -m qualitycheck.bandit_scan HTML_FILE BANDIT_ARGUMENT...
"""

import sys
from pathlib import Path

from bandit.cli import main as bandit_cli
from bandit.core.manager import BanditManager


def main(argv: list[str]) -> None:
    """Run bandit with argv[1:], also writing the HTML report to argv[0]."""
    html, *arguments = argv
    requested = BanditManager.output_results

    def both_reports(manager, lines, sev_level, conf_level, output_file, *formats):
        # Bandit's HTML formatter closes the file it is given.
        report = Path(html).open("w", encoding="utf-8")  # noqa: SIM115
        requested(manager, lines, sev_level, conf_level, report, "html")
        requested(manager, lines, sev_level, conf_level, output_file, *formats)

    BanditManager.output_results = both_reports
    sys.argv = ["bandit", *arguments]
    bandit_cli.main()


if __name__ == "__main__":
    main(sys.argv[1:])
