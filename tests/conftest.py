"""Test cases: inputs in test-cases/<group>/<case>/input/, snapshots in output/."""

import subprocess
from pathlib import Path

import pytest
from check_runs import TEST_CASES, committed_copy, run_check
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "test_cases(group): run once per case in test-cases/<group>/"
    )


def pytest_generate_tests(metafunc):
    marker = metafunc.definition.get_closest_marker("test_cases")
    if marker:
        group = TEST_CASES / marker.args[0]
        case_dirs = sorted(path for path in group.iterdir() if path.is_dir())
        ids = [path.name for path in case_dirs]
        metafunc.parametrize("case_dir", case_dirs, ids=ids)


def _output_extension(output_dir: Path) -> type:
    class OutputFile(SingleFileSnapshotExtension):
        # Bytes, not text: written and compared exactly, LF on every OS.
        _write_mode = WriteMode.BINARY
        file_extension = "txt"

        def serialize(self, data, **kwargs) -> bytes:
            raw = data.encode("utf-8") if isinstance(data, str) else data
            return super().serialize(raw, **kwargs)

        def diff_lines(self, serialized_data, snapshot_data):
            # Compared as bytes, shown as text: a failure lists the changed lines.
            texts = (
                data.decode("utf-8", errors="replace")
                if isinstance(data, bytes)
                else data
                for data in (serialized_data, snapshot_data)
            )
            return super().diff_lines(*texts)

        @classmethod
        def dirname(cls, *, test_location) -> str:
            return str(output_dir)

        @classmethod
        def get_snapshot_name(cls, *, test_location, index=0) -> str:
            return "result"

    return OutputFile


@pytest.fixture
def case(case_dir, snapshot):
    """Return (input_dir, snapshot) of this case; the snapshot is output/result.txt."""
    extension = _output_extension(case_dir / "output")
    return case_dir / "input", snapshot.use_extension(extension)


@pytest.fixture(scope="session")
def checked(tmp_path_factory):
    """Return a function running the check once per case: (project, result)."""
    runs = {}

    def check(case: str) -> tuple[Path, subprocess.CompletedProcess]:
        if case not in runs:
            project = committed_copy(case, tmp_path_factory.mktemp(case) / "p")
            runs[case] = (project, run_check(project))
        return runs[case]

    return check
