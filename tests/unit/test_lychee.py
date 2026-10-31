import pytest
from qualitycheck.lychee import asset, broken_and_unchecked


@pytest.mark.parametrize(
    ("system", "machine", "name"),
    [
        ("Windows", "AMD64", "x86_64-pc-windows-msvc.zip"),
        ("Linux", "x86_64", "x86_64-unknown-linux-musl.tar.gz"),
        ("Linux", "aarch64", "aarch64-unknown-linux-musl.tar.gz"),
        ("Darwin", "arm64", "aarch64-apple-darwin.tar.gz"),
        ("Darwin", "x86_64", "x86_64-apple-darwin.tar.gz"),
    ],
)
def test_one_pinned_asset_per_platform(system, machine, name):
    found = asset(system, machine)
    assert found is not None
    assert found[0] == name
    assert len(found[1]) == 64


def test_no_asset_for_other_platforms():
    assert asset("Linux", "riscv64") is None


def test_client_errors_are_broken_the_network_only_unchecked():
    report = {
        "error_map": {
            "README.md": [
                {
                    "url": "file:///p/missing.md",
                    "status": {"text": "File not found"},
                    "span": {"line": 3},
                },
                {
                    "url": "https://a/x",
                    "status": {
                        "text": "Rejected status code: 404 Not Found",
                        "code": 404,
                    },
                    "span": {"line": 4},
                },
                {
                    "url": "https://a/y",
                    "status": {"text": "Rejected status code: 429", "code": 429},
                    "span": {"line": 5},
                },
                {
                    "url": "https://a/z",
                    "status": {"text": "Rejected status code: 503", "code": 503},
                    "span": {"line": 6},
                },
                {
                    "url": "https://b",
                    "status": {"text": "Network error: connection refused"},
                    "span": {"line": 7},
                },
            ]
        },
        "timeout_map": {
            "README.md": [{"url": "https://c", "status": {"text": "Timeout"}}]
        },
    }
    broken, unchecked = broken_and_unchecked(report)
    assert [(f.line, f.message) for f in broken] == [
        (3, "file:///p/missing.md"),
        (4, "https://a/x"),
    ]
    assert unchecked == 4
