import os
import pathlib

import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import AND, INPUT, NOT, OR


def get_file_path(file_name):
    return str(
        pathlib.Path(os.path.dirname(__file__))
        .joinpath('./benches/')
        .joinpath(file_name)
    )


def test_trivial_instance():

    file_path = get_file_path('test_trivial_instance.bench')
    instance = Circuit().from_bench(file_path)

    assert instance.elements_number == 5
    assert instance.inputs == ['A', 'D', 'E']
    assert instance.outputs == ['C']
    assert instance.input_size == 3
    assert instance.output_size == 1

    assert instance._elements.keys() == {'A', 'D', 'B', 'C', 'E'}
    assert instance.get_element('A').label == 'A'
    assert instance.get_element('A').gate_type == INPUT
    assert instance.get_element('A').operands == ()

    assert instance.get_element('D').label == 'D'
    assert instance.get_element('D').gate_type == INPUT
    assert instance.get_element('D').operands == ()

    assert instance.get_element('E').label == 'E'
    assert instance.get_element('E').gate_type == INPUT
    assert instance.get_element('E').operands == ()

    assert instance.get_element('B').label == 'B'
    assert instance.get_element('B').gate_type == NOT
    assert instance.get_element('B').operands == ('A',)

    assert instance.get_element('C').label == 'C'
    assert instance.get_element('C').gate_type == AND
    assert instance.get_element('C').operands == ('A', 'B')


def test_spaces():

    file_path = get_file_path('test_spaces.bench')
    instance = Circuit().from_bench(file_path)

    assert instance.elements_number == 5
    assert instance.inputs == ['AAAAA', 'DDDD', 'E']
    assert instance.outputs == ['C']
    assert instance.input_size == 3
    assert instance.output_size == 1

    assert instance._elements.keys() == {'AAAAA', 'DDDD', 'B', 'C', 'E'}

    assert instance.get_element('AAAAA').label == 'AAAAA'
    assert instance.get_element('AAAAA').gate_type == INPUT
    assert instance.get_element('AAAAA').operands == ()

    assert instance.get_element('DDDD').label == 'DDDD'
    assert instance.get_element('DDDD').gate_type == INPUT
    assert instance.get_element('DDDD').operands == ()

    assert instance.get_element('E').label == 'E'
    assert instance.get_element('E').gate_type == INPUT
    assert instance.get_element('E').operands == ()

    assert instance.get_element('B').label == 'B'
    assert instance.get_element('B').gate_type == NOT
    assert instance.get_element('B').operands == ('AAAAA',)

    assert instance.get_element('C').label == 'C'
    assert instance.get_element('C').gate_type == AND
    assert instance.get_element('C').operands == ('AAAAA', 'B')


def test_not_init_operands():

    with pytest.raises(CircuitValidationError):
        file_path = get_file_path('test_not_init_operands.bench')
        _ = Circuit().from_bench(file_path)


def test_init_operands_after_using():

    file_path = get_file_path('test_init_operands_after_using.bench')
    instance = Circuit().from_bench(file_path)

    assert instance.elements_number == 3
    assert instance.inputs == ['A']
    assert instance.outputs == ['B']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._elements.keys() == {'A', 'B', 'D'}
    assert instance.get_element('A').label == 'A'
    assert instance.get_element('A').gate_type == INPUT
    assert instance.get_element('A').operands == ()

    assert instance.get_element('B').label == 'B'
    assert instance.get_element('B').gate_type == OR
    assert instance.get_element('B').operands == ('A', 'D')

    assert instance.get_element('D').label == 'D'
    assert instance.get_element('D').gate_type == NOT
    assert instance.get_element('D').operands == ('A',)


def test_sorting():

    file_path = get_file_path('test_sorting.bench')
    instance = Circuit().from_bench(file_path)

    assert instance.elements_number == 5
    assert instance.inputs == ['A', 'D', 'E']
    assert instance.outputs == ['C', 'A']
    assert instance.input_size == 3
    assert instance.output_size == 2

    instance.order_inputs(['E', 'A'])
    assert instance.inputs == ['E', 'A', 'D']

    instance.order_outputs(['A', 'C'])
    assert instance.outputs == ['A', 'C']


def test_top_sort():

    file_path = get_file_path('test_top_sort.bench')
    instance = Circuit().from_bench(file_path)

    assert [elem.label for elem in instance.top_sort()] == [
        '6',
        '4',
        '5',
        '2',
        '3',
        '1',
    ]
    assert [elem.label for elem in instance.top_sort(inversed=True)] == [
        '2',
        '1',
        '4',
        '6',
        '5',
        '3',
    ]


def test_top_sort_several_output():

    file_path = get_file_path('test_top_sort_several_output.bench')
    instance = Circuit().from_bench(file_path)

    assert [elem.label for elem in instance.top_sort()] == [
        '4',
        '6',
        '3',
        '5',
        '2',
        '1',
    ]
    assert [elem.label for elem in instance.top_sort(inversed=True)] == [
        '2',
        '1',
        '5',
        '3',
        '6',
        '4',
    ]


def test_top_sort_empty_circuit():
    instance = Circuit()
    assert list(instance.top_sort()) == []