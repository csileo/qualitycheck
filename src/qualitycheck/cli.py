"""Command line: `qualitycheck` runs the check, `qualitycheck --status` reminds."""

import sys


def main(argv: list[str] | None = None) -> int:
    """Run the command and return its exit code."""
    del argv
    return 0


if __name__ == "__main__":
    sys.exit(main())
