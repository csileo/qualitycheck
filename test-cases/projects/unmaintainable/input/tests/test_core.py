from demo.core import add, chain


def test_add():
    assert add(2, 3) == 5


def test_chain():
    assert chain(1.0) != 0
