# TODO:
#  This file is needed for intermediate representations only. It is not gonna be used in the production.
#  Where to place it? How to format it? Should it be deleted?
import random
import time

from boolean_circuit_tool.core.circuit import Circuit, Gate, Label, AND, OR, NOT, INPUT, IFF
from boolean_circuit_tool.circuits_db.db import CircuitsDatabase

from pathlib import Path
import typing as tp

__all__ = [
    'read_circuit_from_aig_string',
]


def read_circuit_from_aig_string(string: str) -> tp.Optional[Circuit]:
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
    if len(set(output_codes)) != len(output_codes):
        # TODO: handle same outputs correctly. They are skipped for now
        return None
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

    for label in output_labels:
        assert label not in circuit.outputs, \
            f"\nCircuit: \n\t{circuit}\nString:\n\t{string}\nCodes: {output_codes}"
        circuit.mark_as_output(label)

    tt = circuit.get_truth_table()
    assert len(tt) == len(output_codes)
    for i, (table, code) in enumerate(zip(tt, output_codes)):
        table_num = int(''.join(map(lambda x: str(int(x)), reversed(table))), base=2)
        assert table_num == code, \
            f"\nCircuit: \n\t{circuit}\nString:\n\t{string}\nCodes: {output_codes}\nTable num: {table_num} ({i})"

    return circuit


def txt_db_to_bin_db(txt_file: Path, bin_file: Path) -> None:
    db = CircuitsDatabase()
    with txt_file.open("r") as in_stream:
        for i, aig_string in enumerate(in_stream.readlines()):
            circuit = read_circuit_from_aig_string(aig_string)
            if circuit is None:
                continue
            db.add_circuit(circuit, basis='aig')
            if i % 10000 == 0:
                print(f"Processed {i} circuits")
    with bin_file.open("wb") as stream:
        db.save(stream)


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
    # txt_db_to_bin_db(Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db.txt"),
    #                  Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db.bin"))
    timer = time.time()
    with Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db.bin").open("rb") as stream:
        db = CircuitsDatabase(stream)
    duration = time.time() - timer
    print(f"Loading duration: {duration}")

    for i in range(10000000):
        if i % 1000 == 0:
            print(i)
        inputs = random.randint(2, 3)
        outputs = random.randint(1, 3)
        tt = [[random.choice([True, False]) for _ in range(1 << inputs)] for _ in range(outputs)]
        if len(set(map(tuple, tt))) < len(tt):
            continue
        circuit = db.get_by_raw_truth_table(tt)
        assert circuit is not None
        assert circuit.get_truth_table() == tt
