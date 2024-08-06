import pytest

from boolean_circuit_tool.core.dummy import my_sum


@pytest.mark.parametrize(
    'x, y, z',
    [
        (1, 2, 3),
        (10, 5, 15),
    ],
)
def test_sum(x: int, y: int, z: int):
    assert my_sum(x, y) == z
