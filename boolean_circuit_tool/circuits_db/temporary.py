# TODO:
#  This file is needed for intermediate representations only. It is not gonna be used in the production.
#  Where to place it? How to format it? Should it be deleted?

from boolean_circuit_tool.core.circuit import Circuit, Gate, Label, AND, OR, NOT, INPUT, IFF
from boolean_circuit_tool.circuits_db.db import CircuitsDatabase

from pathlib import Path
import typing as tp

__all__ = [
    'read_circuit_from_aig_string',

]


def read_circuit_from_aig_string(string: str) -> Circuit:
    circuit = Circuit()

    tokens = string.split()
    assert all(map(lambda x: all(map(lambda y: y.isdigit(), x)) or x in ('AND', 'NOT'), tokens))

    inputs_count = int(tokens[0])
    input_labels = list(map(_generate_label, range(inputs_count)))
    gates: tp.Dict[Label, Gate] = dict()
    for label in input_labels:
        gate = Gate(label, INPUT)
        gates[label] = gate

    outputs_count = int(tokens[1])
    output_codes = list(map(int, tokens[2:2 + outputs_count]))
    output_labels = list(map(lambda x: _generate_label(int(x)), tokens[2 + outputs_count:2 + 2 * outputs_count]))

    i = 2 + 2 * outputs_count
    gate_id = inputs_count
    while i < len(tokens):
        op = tokens[i]
        assert op in ('AND', 'NOT')
        label = _generate_label(gate_id)
        if op == 'AND':
            assert i + 2 < len(tokens)
            l_operand = _generate_label(int(tokens[i + 1]))
            r_operand = _generate_label(int(tokens[i + 2]))
            i += 3
            gate = Gate(label, AND, (l_operand, r_operand))
        elif op == 'NOT':
            assert i + 1 < len(tokens)
            operand = _generate_label(int(tokens[i + 1]))
            i += 2
            gate = Gate(label, NOT, (operand,))
        else:
            assert False, f"op pos: {i}, op: {op}. Tokens: {tokens}"
        gate_id += 1
        gates[label] = gate

    used: tp.Set[Gate] = set()
    order: tp.List[Gate] = list()
    for gate in gates.values():
        _topology_sort(gate, used, gates, order)
    for gate in order:
        circuit.add_gate(gate)

    # TODO: improve same outputs handling. Do not create output copies
    used_output_labels: tp.Dict[Label, int] = dict()
    for label in output_labels:
        if label in used_output_labels:
            entry_count = used_output_labels[label]
            copy_label = f"{label}_copy_{entry_count}"
            original_gate = gates[label]
            circuit.emplace_gate(copy_label, original_gate.gate_type, original_gate.operands)
            circuit.mark_as_output(copy_label)
            used_output_labels[label] = entry_count + 1
        else:
            circuit.mark_as_output(label)
            used_output_labels[label] = 1

    tt = circuit.get_truth_table()
    assert len(tt) == len(output_codes)
    for table, code in zip(tt, output_codes):
        table_num = int(''.join(map(lambda x: str(int(x)), reversed(table))), base=2)
        assert table_num == code

    return circuit


def txt_db_to_bin_db(txt_file: Path, bin_file: Path) -> None:
    db = CircuitsDatabase()
    with txt_file.open("r") as in_stream:
        for i, aig_string in enumerate(in_stream.readlines()):
            circuit = read_circuit_from_aig_string(aig_string)
            db.add_circuit(circuit, basis='aig')
            if i % 10000 == 0:
                print(f"Processed {i} circuits")
    db.save_to_file(bin_file)


def _generate_label(identifier: int) -> Label:
    return f"gate_{identifier}"


def _topology_sort(gate: Gate, used: tp.Set[Gate], gates: tp.Dict[Label, Gate], order: tp.List[Gate]):
    if gate in used:
        return
    used.add(gate)
    for operand in gate.operands:
        _topology_sort(gates[operand], used, gates, order)
    order.append(gate)


if __name__ == "__main__":
    txt_db_to_bin_db(Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db.txt"),
                     Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db.bin"))
