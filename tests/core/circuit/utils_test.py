import pytest
from boolean_circuit_tool.core.circuit.exceptions import CircuitElementIsAbsentError

from boolean_circuit_tool.core.circuit.utils import (
    input_iterator_with_fixed_sum,
    order_list,
)


def test_input_iterator():
    assert list(input_iterator_with_fixed_sum(3, 0)) == [[False, False, False]]

    _iter = iter(input_iterator_with_fixed_sum(3, 1))
    assert list(next(_iter)) == [True, False, False]
    assert list(next(_iter)) == [False, True, False]
    assert list(next(_iter)) == [False, False, True]

    _iter = iter(input_iterator_with_fixed_sum(3, 2))
    assert list(next(_iter)) == [True, True, False]
    assert list(next(_iter)) == [True, False, True]
    assert list(next(_iter)) == [False, True, True]

    assert list(input_iterator_with_fixed_sum(3, 3)) == [[True, True, True]]


def test_input_iterator_negations():

    negations = [False, True, True]

    assert list(input_iterator_with_fixed_sum(3, 0, negations=negations)) == [
        [False, True, True]
    ]

    _iter = iter(input_iterator_with_fixed_sum(3, 1, negations=negations))
    assert list(next(_iter)) == [True, True, True]
    assert list(next(_iter)) == [False, False, True]
    assert list(next(_iter)) == [False, True, False]

    _iter = iter(input_iterator_with_fixed_sum(3, 2, negations=negations))
    assert list(next(_iter)) == [True, False, True]
    assert list(next(_iter)) == [True, True, False]
    assert list(next(_iter)) == [False, False, False]

    assert list(input_iterator_with_fixed_sum(3, 3, negations=negations)) == [
        [True, False, False]
    ]


def test_order_list():

    assert order_list([], []) == []
    assert order_list(['3', '1'], ['1', '2', '3']) == ['3', '1', '2']
    assert order_list(['3', '2', '1'], ['1', '2', '3']) == ['3', '2', '1']
    assert order_list(['3', '2', '1'], ['3', '3', '2', '3', '1']) == [
        '3',
        '2',
        '1',
        '3',
        '3',
    ]

    with pytest.raises(CircuitElementIsAbsentError):
        order_list(['1', '4'], ['1', '2', '3'])
