from qualitycheck.history import COLUMNS, append, last_pass, parse


def row(commit: str, result: str) -> dict[str, str]:
    return {
        **dict.fromkeys(COLUMNS, "0"),
        "commit": commit,
        "result": result,
        "date": "d-" + commit,
    }


def test_append_starts_with_the_header_and_keeps_old_rows():
    first = append("", row("a", "PASS"))
    assert first.splitlines()[0] == ";".join(COLUMNS)
    second = append(first, row("b", "FAIL"))
    assert second.startswith(first)
    assert [r["commit"] for r in parse(second)] == ["a", "b"]


def test_last_pass_skips_failures():
    rows = parse(append(append("", row("a", "PASS")), row("b", "FAIL")))
    assert last_pass(rows)["commit"] == "a"
    assert last_pass(parse(append("", row("b", "FAIL")))) is None


def test_parse_empty():
    assert parse("") == []
