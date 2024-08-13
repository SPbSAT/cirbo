import typing as tp
import uuid

from boolean_circuit_tool.core.circuit import gate

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Circuit

__all__ = ['convert_gate']


def convert_gate(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert gate in the circuit to bench format.

    If the corresponding conversion function is not specified for a given gate type, we
    assume that the gate is already in bench format.

    (!!!) Conversion ALWAYS_TRUE and ALWAYS_FALSE requires the presence of at least one
    input in the circuit. Since it is with the use of this input these type of gates
    will be replaced with subcircuit.

    """
    if _gate.gate_type in _convertors:
        _convertors[_gate.gate_type](_gate, circuit)


def _convert_lt(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LT(x, y) to AND(NOT(x), y)."""
    new_gate_label = 'new_gate_LT_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[0],))

    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.AND, (new_gate_label, _gate.operands[1])
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_leq(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LEQ(x, y) to OR(NOT(x), y)."""
    new_gate_label = 'new_gate_LEQ_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[0],))

    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.OR, (new_gate_label, _gate.operands[1])
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_gt(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert GT(x, y) to AND(x, NOT(y))."""
    new_gate_label = 'new_gate_GT_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[1],))

    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.AND, (_gate.operands[0], new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_geq(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert GEQ(x, y) to OR(x, NOT(y))."""
    new_gate_label = 'new_gate_GEQ_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[1],))

    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.OR, (_gate.operands[0], new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_liff(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LIFF(x, y) to IFF(x)"""
    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.IFF, (_gate.operands[0],))


def _convert_riff(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert RIFF(x, y) to IFF(y)"""
    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.IFF, (_gate.operands[1],))


def _convert_lnot(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LNOT(x, y) to NOT(x)"""
    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (_gate.operands[0],))


def _convert_rnot(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert RNOT(x, y) to NOT(y)"""
    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (_gate.operands[1],))


def _convert_always_true(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert ALWAYS_TRUE to OR(x, NOT(x)), where x is the first inputs in circuit.

    If the circuit hasn't any inputs the algorithm raises.

    """
    first_input = circuit.input_at_index(0)

    new_gate_label = 'new_gate_ALWAYS_TRUE_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (first_input,))

    circuit._add_user(first_input, _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.OR, (first_input, new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_always_false(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert ALWAYS_FALSE to AND(x, NOT(x)), where x is the first inputs in circuit.

    If the circuit hasn't any inputs the algorithm raises.

    """
    first_input = circuit.input_at_index(0)

    new_gate_label = 'new_gate_ALWAYS_FALSE_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (first_input,))

    circuit._add_user(first_input, _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.AND, (first_input, new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


_convertors: dict[gate.GateType, tp.Callable[[gate.Gate, 'Circuit'], None]] = {
    gate.LT: _convert_lt,
    gate.LEQ: _convert_leq,
    gate.GT: _convert_gt,
    gate.GEQ: _convert_geq,
    gate.LIFF: _convert_liff,
    gate.RIFF: _convert_riff,
    gate.LNOT: _convert_lnot,
    gate.RNOT: _convert_rnot,
    gate.ALWAYS_TRUE: _convert_always_true,
    gate.ALWAYS_FALSE: _convert_always_false,
}


def _add_new_gate_to_blocks(
    old_gate_label: gate.Label, new_gate_label: gate.Label, circuit: 'Circuit'
):
    """Add new gate to circuit's blocks, if their gates has old_gate_label."""
    for block in circuit.blocks.values():
        if old_gate_label in block.gates:
            block._gates.append(new_gate_label)
