from demo.first import first
from demo.second import second


def test_sums():
    assert first([1, -2]) == second([1, -2])
