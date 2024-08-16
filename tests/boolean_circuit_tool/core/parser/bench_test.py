import os
import pathlib
import unittest
import unittest.mock

import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    GEQ,
    GT,
    IFF,
    INPUT,
    LEQ,
    LIFF,
    LNOT,
    LT,
    NAND,
    NOR,
    NOT,
    NXOR,
    OR,
    RIFF,
    RNOT,
    XOR,
)


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
    assert instance.gates_number() == 1
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
    assert [elem.label for elem in instance.top_sort(inverse=True)] == [
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
    assert [elem.label for elem in instance.top_sort(inverse=True)] == [
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
    dfs_mock_on_discover_hook = unittest.mock.Mock(return_value=None)
    dfs_mock_on_dfs_end_hook = unittest.mock.Mock(return_value=None)
    assert [
        elem.label
        for elem in instance.dfs(
            inverse=False,
            on_enter_hook=dfs_mock_on_enter_hook,
            on_exit_hook=dfs_mock_on_exit_hook,
            unvisited_hook=dfs_mock_unvisited_hook,
            on_discover_hook=dfs_mock_on_discover_hook,
            on_dfs_end_hook=dfs_mock_on_dfs_end_hook,
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
    assert dfs_mock_on_discover_hook.call_count == 5
    assert dfs_mock_on_dfs_end_hook.call_count == 1

    bfs_mock_on_enter_hook = unittest.mock.Mock(return_value=None)
    bfs_mock_unvisited_hook = unittest.mock.Mock(return_value=None)
    bfs_mock_on_discover_hook = unittest.mock.Mock(return_value=None)
    bfs_mock_on_dfs_end_hook = unittest.mock.Mock(return_value=None)
    assert [
        elem.label
        for elem in instance.bfs(
            inverse=False,
            on_enter_hook=bfs_mock_on_enter_hook,
            unvisited_hook=bfs_mock_unvisited_hook,
            on_discover_hook=bfs_mock_on_discover_hook,
            on_dfs_end_hook=bfs_mock_on_dfs_end_hook,
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
    assert bfs_mock_on_discover_hook.call_count == 5
    assert bfs_mock_on_dfs_end_hook.call_count == 1


def test_all_types_of_gate():
    file_path = get_file_path('test_all_types_of_gate.bench')
    instance = Circuit().from_bench_file(file_path)

    assert instance.size == 21
    assert instance.gates_number([]) == 21
    assert instance.inputs == ['1', '2']
    assert instance.outputs == ['21']
    assert instance.input_size == 2
    assert instance.output_size == 1

    assert instance._gates.keys() == {
        '1',
        '2',
        '3',
        '4',
        '5',
        '6',
        '7',
        '8',
        '9',
        '10',
        '11',
        '12',
        '13',
        '14',
        '15',
        '16',
        '17',
        '18',
        '19',
        '20',
        '21',
    }

    assert instance.get_gate('1').label == '1'
    assert instance.get_gate('1').gate_type == INPUT
    assert instance.get_gate('1').operands == ()
    assert instance.get_gate_users('1') == ['3', '4', '5']

    assert instance.get_gate('2').label == '2'
    assert instance.get_gate('2').gate_type == INPUT
    assert instance.get_gate('2').operands == ()
    assert instance.get_gate_users('2') == ['4', '5', '6', '11', '12', '15']

    assert instance.get_gate('3').label == '3'
    assert instance.get_gate('3').gate_type == NOT
    assert instance.get_gate('3').operands == ('1',)
    assert instance.get_gate_users('3') == ['9']

    assert instance.get_gate('4').label == '4'
    assert instance.get_gate('4').gate_type == AND
    assert instance.get_gate('4').operands == ('1', '2')
    assert instance.get_gate_users('4') == ['6', '10', '11']

    assert instance.get_gate('5').label == '5'
    assert instance.get_gate('5').gate_type == XOR
    assert instance.get_gate('5').operands == ('1', '2')
    assert instance.get_gate_users('5') == ['14', '19']

    assert instance.get_gate('6').label == '6'
    assert instance.get_gate('6').gate_type == OR
    assert instance.get_gate('6').operands == ('2', '4')
    assert instance.get_gate_users('6') == ['18', '19']

    assert instance.get_gate('7').label == '7'
    assert instance.get_gate('7').gate_type == ALWAYS_FALSE
    assert instance.get_gate('7').operands == ()
    assert instance.get_gate_users('7') == ['9']

    assert instance.get_gate('8').label == '8'
    assert instance.get_gate('8').gate_type == ALWAYS_TRUE
    assert instance.get_gate('8').operands == ()
    assert instance.get_gate_users('8') == ['10', '17']

    assert instance.get_gate('9').label == '9'
    assert instance.get_gate('9').gate_type == LNOT
    assert instance.get_gate('9').operands == ('7', '3')
    assert instance.get_gate_users('9') == []

    assert instance.get_gate('10').label == '10'
    assert instance.get_gate('10').gate_type == RNOT
    assert instance.get_gate('10').operands == ('4', '8')
    assert instance.get_gate_users('10') == []

    assert instance.get_gate('11').label == '11'
    assert instance.get_gate('11').gate_type == LEQ
    assert instance.get_gate('11').operands == ('2', '4')
    assert instance.get_gate_users('11') == ['12', '13']

    assert instance.get_gate('12').label == '12'
    assert instance.get_gate('12').gate_type == LT
    assert instance.get_gate('12').operands == ('2', '11')
    assert instance.get_gate_users('12') == ['13']

    assert instance.get_gate('13').label == '13'
    assert instance.get_gate('13').gate_type == GEQ
    assert instance.get_gate('13').operands == ('11', '12')
    assert instance.get_gate_users('13') == ['14', '17']

    assert instance.get_gate('14').label == '14'
    assert instance.get_gate('14').gate_type == GT
    assert instance.get_gate('14').operands == ('13', '5')
    assert instance.get_gate_users('14') == ['15', '16']

    assert instance.get_gate('15').label == '15'
    assert instance.get_gate('15').gate_type == NAND
    assert instance.get_gate('15').operands == ('14', '2')
    assert instance.get_gate_users('15') == ['16']

    assert instance.get_gate('16').label == '16'
    assert instance.get_gate('16').gate_type == NOR
    assert instance.get_gate('16').operands == ('14', '15')
    assert instance.get_gate_users('16') == []

    assert instance.get_gate('17').label == '17'
    assert instance.get_gate('17').gate_type == NXOR
    assert instance.get_gate('17').operands == ('13', '8')
    assert instance.get_gate_users('17') == ['18']

    assert instance.get_gate('18').label == '18'
    assert instance.get_gate('18').gate_type == LIFF
    assert instance.get_gate('18').operands == ('17', '6')
    assert instance.get_gate_users('18') == []

    assert instance.get_gate('19').label == '19'
    assert instance.get_gate('19').gate_type == RIFF
    assert instance.get_gate('19').operands == ('5', '6')
    assert instance.get_gate_users('19') == ['20']

    assert instance.get_gate('20').label == '20'
    assert instance.get_gate('20').gate_type == IFF
    assert instance.get_gate('20').operands == ('19',)
    assert instance.get_gate_users('20') == ['21']

    assert instance.get_gate('21').label == '21'
    assert instance.get_gate('21').gate_type == IFF
    assert instance.get_gate('21').operands == ('20',)
    assert instance.get_gate_users('21') == []
