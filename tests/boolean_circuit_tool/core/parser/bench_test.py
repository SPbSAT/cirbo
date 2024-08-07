import os
import pathlib
import unittest
import unittest.mock

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
    instance = Circuit().from_bench_file(file_path)

    assert instance.size == 5
    assert instance.gates_number == 1
    assert instance.inputs == ['A', 'D', 'E']
    assert instance.outputs == ['C']
    assert instance.input_size == 3
    assert instance.output_size == 1

    assert instance._gates.keys() == {'A', 'D', 'B', 'C', 'E'}
    assert instance.get_gate('A').label == 'A'
    assert instance.get_gate('A').gate_type == INPUT
    assert instance.get_gate('A').operands == ()

    assert instance.get_gate('D').label == 'D'
    assert instance.get_gate('D').gate_type == INPUT
    assert instance.get_gate('D').operands == ()

    assert instance.get_gate('E').label == 'E'
    assert instance.get_gate('E').gate_type == INPUT
    assert instance.get_gate('E').operands == ()

    assert instance.get_gate('B').label == 'B'
    assert instance.get_gate('B').gate_type == NOT
    assert instance.get_gate('B').operands == ('A',)

    assert instance.get_gate('C').label == 'C'
    assert instance.get_gate('C').gate_type == AND
    assert instance.get_gate('C').operands == ('A', 'B')


def test_spaces():

    file_path = get_file_path('test_spaces.bench')
    instance = Circuit().from_bench_file(file_path)

    assert instance.size == 5
    assert instance.inputs == ['AAAAA', 'DDDD', 'E']
    assert instance.outputs == ['C']
    assert instance.input_size == 3
    assert instance.output_size == 1

    assert instance._gates.keys() == {'AAAAA', 'DDDD', 'B', 'C', 'E'}

    assert instance.get_gate('AAAAA').label == 'AAAAA'
    assert instance.get_gate('AAAAA').gate_type == INPUT
    assert instance.get_gate('AAAAA').operands == ()

    assert instance.get_gate('DDDD').label == 'DDDD'
    assert instance.get_gate('DDDD').gate_type == INPUT
    assert instance.get_gate('DDDD').operands == ()

    assert instance.get_gate('E').label == 'E'
    assert instance.get_gate('E').gate_type == INPUT
    assert instance.get_gate('E').operands == ()

    assert instance.get_gate('B').label == 'B'
    assert instance.get_gate('B').gate_type == NOT
    assert instance.get_gate('B').operands == ('AAAAA',)

    assert instance.get_gate('C').label == 'C'
    assert instance.get_gate('C').gate_type == AND
    assert instance.get_gate('C').operands == ('AAAAA', 'B')


def test_not_init_operands():

    with pytest.raises(CircuitValidationError):
        file_path = get_file_path('test_not_init_operands.bench')
        _ = Circuit().from_bench_file(file_path)


def test_init_operands_after_using():

    file_path = get_file_path('test_init_operands_after_using.bench')
    instance = Circuit().from_bench_file(file_path)

    assert instance.size == 3
    assert instance.inputs == ['A']
    assert instance.outputs == ['B']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._gates.keys() == {'A', 'B', 'D'}
    assert instance.get_gate('A').label == 'A'
    assert instance.get_gate('A').gate_type == INPUT
    assert instance.get_gate('A').operands == ()

    assert instance.get_gate('B').label == 'B'
    assert instance.get_gate('B').gate_type == OR
    assert instance.get_gate('B').operands == ('A', 'D')

    assert instance.get_gate('D').label == 'D'
    assert instance.get_gate('D').gate_type == NOT
    assert instance.get_gate('D').operands == ('A',)


def test_sorting():

    file_path = get_file_path('test_sorting.bench')
    instance = Circuit().from_bench_file(file_path)

    assert instance.size == 5
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
    instance = Circuit().from_bench_file(file_path)

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
    instance = Circuit().from_bench_file(file_path)

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


def test_traverse_circuit_circuit():

    file_path = get_file_path('test_top_sort_several_output.bench')
    instance = Circuit().from_bench_file(file_path)

    assert [elem.label for elem in instance.dfs(inverse=False)] == [
        '4',
        '6',
        '3',
        '1',
        '2',
    ]
    assert [elem.label for elem in instance.dfs(inverse=True)] == [
        '2',
        '6',
        '4',
        '5',
        '1',
        '3',
    ]
    assert [elem.label for elem in instance.bfs(inverse=False)] == [
        '6',
        '4',
        '2',
        '3',
        '1',
    ]
    assert [elem.label for elem in instance.bfs(inverse=True)] == [
        '1',
        '2',
        '3',
        '5',
        '4',
        '6',
    ]
    assert [elem.label for elem in instance.bfs(['1'], inverse=True)] == [
        '1',
        '3',
        '5',
        '4',
        '6',
    ]

    dfs_mock_on_enter_hook = unittest.mock.Mock(return_value=None)
    dfs_mock_on_exit_hook = unittest.mock.Mock(return_value=None)
    dfs_mock_unvisited_hook = unittest.mock.Mock(return_value=None)
    assert [
        elem.label
        for elem in instance.dfs(
            inverse=False,
            on_enter_hook=dfs_mock_on_enter_hook,
            on_exit_hook=dfs_mock_on_exit_hook,
            unvisited_hook=dfs_mock_unvisited_hook,
        )
    ] == [
        '4',
        '6',
        '3',
        '1',
        '2',
    ]
    assert dfs_mock_on_enter_hook.call_count == 5
    assert dfs_mock_on_exit_hook.call_count == 5
    assert dfs_mock_unvisited_hook.call_count == 1

    bfs_mock_on_enter_hook = unittest.mock.Mock(return_value=None)
    bfs_mock_unvisited_hook = unittest.mock.Mock(return_value=None)
    assert [
        elem.label
        for elem in instance.bfs(
            inverse=False,
            on_enter_hook=bfs_mock_on_enter_hook,
            unvisited_hook=bfs_mock_unvisited_hook,
        )
    ] == [
        '6',
        '4',
        '2',
        '3',
        '1',
    ]
    assert bfs_mock_on_enter_hook.call_count == 5
    assert bfs_mock_unvisited_hook.call_count == 1
