import pytest

from qualitycheck.settings import SettingsError, load


@pytest.mark.test_cases("settings")
def test_settings(case):
    input_dir, snapshot = case
    try:
        found = repr(load(input_dir))
    except SettingsError as error:
        found = f"rejected: {error}"
    assert found + "\n" == snapshot
