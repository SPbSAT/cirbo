import copy

import mock
import pytest

from cirbo.core.circuit import Circuit, gate, GateType, Label
from cirbo.core.circuit.transformer import Transformer


@pytest.fixture(scope='function')
def simple_circuit_1():
    circuit = Circuit.bare_circuit(1)
    circuit.emplace_gate('NOT', gate.NOT, (circuit.inputs[0],))
    circuit.emplace_gate('AND', gate.AND, (circuit.inputs[0], 'NOT'))
    circuit.set_outputs(['AND'])
    return circuit


@pytest.fixture(scope='function')
def simple_circuit_2():
    circuit = Circuit.bare_circuit(3)
    circuit.emplace_gate('AND', gate.AND, (circuit.inputs[0], circuit.inputs[1]))
    circuit.emplace_gate('OR', gate.OR, (circuit.inputs[1], circuit.inputs[2]))
    circuit.emplace_gate('XOR', gate.XOR, ('AND', 'OR'))
    circuit.set_outputs(['XOR'])
    return circuit


class DummyIdTransformer(Transformer):
    def _transform(self, circuit: Circuit) -> Circuit:
        _new_circuit = copy.copy(circuit)
        return _new_circuit


class DummyIdIdempotentTransformer(Transformer):
    __idempotent__ = True

    def _transform(self, circuit: Circuit) -> Circuit:
        _new_circuit = copy.copy(circuit)
        return _new_circuit


class DummyNewOutputTransformer(Transformer):
    def __init__(self, label: Label, gate_type: GateType, operands: tuple[Label, ...]):
        super().__init__()
        self._label = label
        self._gate_type = gate_type
        self._gate_operands = operands

    def _transform(self, circuit: Circuit) -> Circuit:
        _new_circuit = copy.copy(circuit)
        _new_circuit.emplace_gate(self._label, self._gate_type, self._gate_operands)
        _new_circuit.set_outputs([self._label])
        return _new_circuit


class DummySetNoOutputsTransformer(Transformer):
    def _transform(self, circuit: Circuit) -> Circuit:
        _new_circuit = copy.copy(circuit)
        _new_circuit.set_outputs([])
        return _new_circuit


class DummyWithPrePostTransformer(Transformer):
    def __init__(self):
        super().__init__(
            pre_transformers=(DummyIdTransformer(), DummySetNoOutputsTransformer()),
            post_transformers=(DummyIdTransformer(),),
        )

    def _transform(self, circuit: Circuit) -> Circuit:
        _new_circuit = copy.copy(circuit)
        return _new_circuit


class DummyWithCompositePrePostTransformer(Transformer):
    def __init__(self):
        super().__init__(
            pre_transformers=(DummyWithPrePostTransformer(),),
            post_transformers=(DummyIdTransformer(),),
        )

    def _transform(self, circuit: Circuit) -> Circuit:
        _new_circuit = copy.copy(circuit)
        return _new_circuit


def test_simple_transformers_transform_works(simple_circuit_1, simple_circuit_2):
    id_t = DummyIdTransformer()
    assert simple_circuit_1 == id_t.transform(simple_circuit_1)
    assert simple_circuit_2 == id_t.transform(simple_circuit_2)

    no_t_1 = DummyNewOutputTransformer('GEQ', gate.GEQ, ("0", "AND"))
    _new_output_circuit_1 = no_t_1.transform(simple_circuit_1)
    assert _new_output_circuit_1.size == simple_circuit_1.size + 1
    assert _new_output_circuit_1.has_gate('GEQ')
    assert _new_output_circuit_1.get_gate('GEQ').gate_type == gate.GEQ
    assert _new_output_circuit_1.outputs == ['GEQ']

    no_t_2 = DummyNewOutputTransformer('GEQ', gate.GEQ, ("0", "1"))
    _new_output_circuit_2 = no_t_2.transform(simple_circuit_2)
    assert _new_output_circuit_2.size == simple_circuit_2.size + 1
    assert _new_output_circuit_2.has_gate('GEQ')
    assert _new_output_circuit_2.get_gate('GEQ').gate_type == gate.GEQ
    assert _new_output_circuit_2.outputs == ['GEQ']


def test_transformers_composition_pipes():
    id_t = DummyIdTransformer()
    no_t = DummyNewOutputTransformer('GEQ', gate.GEQ, ("0", "1"))
    tc_l = (id_t | no_t) | id_t
    tc_r = id_t | (no_t | id_t)

    assert list(map(type, tc_l.transformers)) == [
        DummyIdTransformer,
        DummyNewOutputTransformer,
        DummyIdTransformer,
    ]
    assert list(map(type, tc_r.transformers)) == [
        DummyIdTransformer,
        DummyNewOutputTransformer,
        DummyIdTransformer,
    ]


def test_transformers_composition_transform_works_one(simple_circuit_1):
    id_t = DummyIdTransformer()
    sno_t = DummySetNoOutputsTransformer()

    no_t_1 = DummyNewOutputTransformer('GEQ', gate.GEQ, ("0", "AND"))
    comp_1_1 = id_t | sno_t | id_t
    comp_1_2 = comp_1_1 | no_t_1
    comp_1_3 = comp_1_1 | sno_t
    _new_output_circuit_1_1 = comp_1_1.transform(simple_circuit_1)
    assert _new_output_circuit_1_1.size == simple_circuit_1.size
    assert _new_output_circuit_1_1.outputs == []
    _new_output_circuit_1_2 = comp_1_2.transform(_new_output_circuit_1_1)
    assert _new_output_circuit_1_2.size == _new_output_circuit_1_1.size + 1
    assert _new_output_circuit_1_2.has_gate('GEQ')
    assert _new_output_circuit_1_2.get_gate('GEQ').gate_type == gate.GEQ
    assert _new_output_circuit_1_2.outputs == ['GEQ']
    _new_output_circuit_1_3 = comp_1_3.transform(_new_output_circuit_1_2)
    assert _new_output_circuit_1_3.size == _new_output_circuit_1_2.size
    assert _new_output_circuit_1_3.has_gate('GEQ')
    assert _new_output_circuit_1_3.get_gate('GEQ').gate_type == gate.GEQ
    assert _new_output_circuit_1_3.outputs == []

    assert _new_output_circuit_1_1 is not _new_output_circuit_1_2
    assert _new_output_circuit_1_1 is not _new_output_circuit_1_3
    assert _new_output_circuit_1_2 is not _new_output_circuit_1_3


def test_transformers_composition_transform_works_two(simple_circuit_2):
    id_t = DummyIdTransformer()
    sno_t = DummySetNoOutputsTransformer()

    no_t_2 = DummyNewOutputTransformer('GEQ', gate.GEQ, ("0", "1"))
    comp_2_1 = id_t | sno_t | id_t
    comp_2_2 = comp_2_1 | no_t_2
    comp_2_3 = comp_2_1 | sno_t
    _new_output_circuit_2_1 = comp_2_1.transform(simple_circuit_2)
    assert _new_output_circuit_2_1.size == simple_circuit_2.size
    assert _new_output_circuit_2_1.outputs == []
    _new_output_circuit_2_2 = comp_2_2.transform(_new_output_circuit_2_1)
    assert _new_output_circuit_2_2.size == _new_output_circuit_2_1.size + 1
    assert _new_output_circuit_2_2.has_gate('GEQ')
    assert _new_output_circuit_2_2.get_gate('GEQ').gate_type == gate.GEQ
    assert _new_output_circuit_2_2.outputs == ['GEQ']
    _new_output_circuit_2_3 = comp_2_3.transform(_new_output_circuit_2_2)
    assert _new_output_circuit_2_3.size == _new_output_circuit_2_2.size
    assert _new_output_circuit_2_3.has_gate('GEQ')
    assert _new_output_circuit_2_3.get_gate('GEQ').gate_type == gate.GEQ
    assert _new_output_circuit_2_3.outputs == []

    assert _new_output_circuit_2_1 is not _new_output_circuit_2_2
    assert _new_output_circuit_2_1 is not _new_output_circuit_2_3
    assert _new_output_circuit_2_2 is not _new_output_circuit_2_3


def test_linearize_transformers():
    assert list(
        map(
            type,
            Transformer.linearize_transformers(
                [DummyWithCompositePrePostTransformer()]
            ),
        )
    ) == [
        DummyIdTransformer,
        DummySetNoOutputsTransformer,
        DummyWithPrePostTransformer,
        DummyIdTransformer,
        DummyWithCompositePrePostTransformer,
        DummyIdTransformer,
    ]


def test_linearize_reduce_transformers():
    assert list(
        map(
            type,
            Transformer.linearize_reduce_transformers(
                [
                    DummyIdIdempotentTransformer(),
                ]
            ),
        )
    ) == [
        DummyIdIdempotentTransformer,
    ]
    assert list(
        map(
            type,
            Transformer.linearize_reduce_transformers(
                [
                    DummyIdIdempotentTransformer(),
                    DummyIdIdempotentTransformer(),
                    DummyIdIdempotentTransformer(),
                ]
            ),
        )
    ) == [
        DummyIdIdempotentTransformer,
    ]
    assert list(
        map(
            type,
            Transformer.linearize_reduce_transformers(
                [
                    DummyIdIdempotentTransformer(),
                    DummyIdTransformer(),
                    DummyIdIdempotentTransformer(),
                    DummyIdIdempotentTransformer(),
                ]
            ),
        )
    ) == [
        DummyIdIdempotentTransformer,
        DummyIdTransformer,
        DummyIdIdempotentTransformer,
    ]


def test_pre_post_are_called():
    i = 1

    def _order(*_, **__):
        nonlocal i
        i += 1
        return i

    with (
        mock.patch.object(
            DummyIdTransformer,
            '_transform',
            side_effect=_order,
        ) as id_patch,
        mock.patch.object(
            DummySetNoOutputsTransformer,
            '_transform',
            side_effect=_order,
        ) as sno_patch,
        mock.patch.object(
            DummyWithPrePostTransformer,
            '_transform',
            side_effect=_order,
        ) as prepost_patch,
    ):
        _ = DummyWithPrePostTransformer().transform(1)

        id_patch.assert_has_calls([mock.call(1), mock.call(4)], any_order=False)
        sno_patch.assert_has_calls([mock.call(2)], any_order=False)
        prepost_patch.assert_has_calls([mock.call(3)], any_order=False)


def test_pre_post_are_called_composite(simple_circuit_1):
    i = 1

    def _order(self, *_, **__):
        print(self)
        nonlocal i
        i += 1
        return i

    with (
        mock.patch.object(
            DummyIdTransformer,
            '_transform',
            side_effect=_order,
        ) as id_patch,
        mock.patch.object(
            DummySetNoOutputsTransformer,
            '_transform',
            side_effect=_order,
        ) as sno_patch,
        mock.patch.object(
            DummyWithPrePostTransformer,
            '_transform',
            side_effect=_order,
        ) as prepost_patch,
        mock.patch.object(
            DummyWithCompositePrePostTransformer,
            '_transform',
            side_effect=_order,
        ) as comp_patch,
    ):
        _ = DummyWithCompositePrePostTransformer().transform(1)

        id_patch.assert_has_calls(
            [mock.call(1), mock.call(4), mock.call(6)], any_order=False
        )
        sno_patch.assert_has_calls([mock.call(2)], any_order=False)
        prepost_patch.assert_has_calls([mock.call(3)], any_order=False)
        comp_patch.assert_has_calls([mock.call(5)], any_order=False)
