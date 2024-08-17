import logging
import operator
import typing as tp

import more_itertools

from boolean_circuit_tool.core.circuit import Circuit, Gate, gate, Label
from boolean_circuit_tool.core.circuit.transformer import Transformer
from boolean_circuit_tool.minimization.simplification.remove_redundant_gates import (
    RemoveRedundantGates,
)


__all__ = [
    'CollapseUnaryOperators',
]


logger = logging.getLogger(__name__)


# Utility that helps to extract significant operand.
_unary_to_operand_getter = {
    gate.NOT: operator.itemgetter(0),
    gate.LNOT: operator.itemgetter(0),
    gate.RNOT: operator.itemgetter(1),
    gate.IFF: operator.itemgetter(0),
    gate.LIFF: operator.itemgetter(0),
    gate.RIFF: operator.itemgetter(1),
}


class CollapseUnaryOperators(Transformer):
    """
    Simplifies the circuit by collapsing consecutive unary gates . Collapses double NOTs
    A = NOT(NOT(B)) => A = B and eliminates IFFs.

    Traverses the circuit recursively, starting from the output gates, and rebuilds
    the circuit collapsing paths through redundant unary gates.

    Notes: Output gates labels may change after this method is applied, but their
    order will be preserved.

    Note: gates are not removed after this method is applied, and only operands of
    gates are revamped. It is recommended to call `RemoveRedundantGates` right
    after this method.

    Note: will also remap LNOT, RNOT, LIFF, RIFF to their transitive significant
    operand if path reduction is possible.

    """

    def __init__(self):
        super().__init__(post_transformers=(RemoveRedundantGates(),))

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        _new_circuit = Circuit()

        # redirection links that will
        # allow us to collapse paths.
        #
        # contains to predecessor path to which consists of even number of NOTs
        _not_to_even_parent: dict[Label, Label] = {}
        # contains to predecessor path to which consists of odd number of NOTs
        _not_to_odd_parent: dict[Label, Label] = {}
        # contains to predecessor path to which consists of only of IFFs
        _iff_to_parent: dict[Label, Label] = {}

        # iterate from inputs to outputs in topsort
        # order to collect redirection links.
        for _gate in circuit.top_sort(inverse=True):
            if (
                False
                or _gate.gate_type == gate.NOT
                or _gate.gate_type == gate.LNOT
                or _gate.gate_type == gate.RNOT
            ):
                _oper = _unary_to_operand_getter[_gate.gate_type](_gate.operands)
                if _oper in _not_to_odd_parent:
                    _not_to_even_parent[_gate.label] = _not_to_odd_parent[_oper]
                _not_to_odd_parent[_gate.label] = _not_to_even_parent.get(_oper, _oper)

            if (
                False
                or _gate.gate_type == gate.IFF
                or _gate.gate_type == gate.LIFF
                or _gate.gate_type == gate.RIFF
            ):
                _oper = _unary_to_operand_getter[_gate.gate_type](_gate.operands)
                _iff_to_parent[_gate.label] = _iff_to_parent.get(_oper, _oper)

        # remap gates to equivalent but closer ones.
        def _remap_gate(gate_label: Label):
            nonlocal circuit, _not_to_even_parent, _iff_to_parent
            _op_gate = circuit.get_gate(gate_label)

            if (
                False
                or _op_gate.gate_type == gate.NOT
                or _op_gate.gate_type == gate.LNOT
                or _op_gate.gate_type == gate.RNOT
            ):
                return _not_to_even_parent.get(gate_label, gate_label)
            elif (
                False
                or _op_gate.gate_type == gate.IFF
                or _op_gate.gate_type == gate.LIFF
                or _op_gate.gate_type == gate.RIFF
            ):
                return _iff_to_parent.get(gate_label, gate_label)
            else:
                return gate_label

        # rebuild circuit from inputs to outputs with remapping.
        def _on_exit_hook_impl(_gate: Gate, _: tp.Mapping):
            nonlocal _new_circuit, _not_to_even_parent, _iff_to_parent
            _new_circuit.emplace_gate(
                label=_gate.label,
                gate_type=_gate.gate_type,
                operands=tuple(map(_remap_gate, _gate.operands)),
            )

        # reconstruct circuit
        more_itertools.consume(
            circuit.dfs(
                circuit.outputs,
                on_exit_hook=_on_exit_hook_impl,
            )
        )

        # reorder inputs according to original order
        _new_circuit.set_inputs(circuit.inputs)

        # mark outputs in new circuit by remapping them to their equivalent ones.
        _new_circuit.set_outputs(list(map(_remap_gate, circuit.outputs)))

        return _new_circuit
