from demo.core import add, grade


def test_add():
    assert add(2, 3) == 5


def test_grade():
    assert grade(3) == 30
