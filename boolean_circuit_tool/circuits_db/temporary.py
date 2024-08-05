# TODO:
#  This file is needed for intermediate representations only.
#  It is not gonna be used in the production.
#  Where to place it? How to format it? Should it be deleted?
import random

# import time
import typing as tp
from pathlib import Path

from boolean_circuit_tool.circuits_db.db import CircuitsDatabase

from boolean_circuit_tool.circuits_db.exceptions import CircuitsDatabaseError
from boolean_circuit_tool.core.circuit import (
    AND,
    Circuit,
    Gate,
    GEQ,
    GT,
    IFF,
    INPUT,
    Label,
    LEQ,
    LT,
    NAND,
    NOR,
    NOT,
    NXOR,
    OR,
    XOR,
)

__all__ = [
    'read_circuit_from_string',
]

_gate_types = {
    gate.name: gate
    for gate in [
        AND,
        GEQ,
        GT,
        IFF,
        LEQ,
        LT,
        NAND,
        NOR,
        NOT,
        NXOR,
        OR,
        XOR,
    ]
}


def read_circuit_from_string(string: str) -> tp.Optional[Circuit]:
    circuit = Circuit()

    tokens = string.split()
    assert all(
        map(
            lambda x: all(map(lambda y: y.isdigit(), x)) or x in _gate_types.keys(),
            tokens,
        )
    )

    inputs_count = int(tokens[0])
    input_labels = list(map(_generate_label, range(inputs_count)))
    gates: tp.Dict[Label, Gate] = dict()
    for label in input_labels:
        gate = Gate(label, INPUT)
        gates[label] = gate

    outputs_count = int(tokens[1])
    output_codes = list(map(int, tokens[2 : 2 + outputs_count]))
    if len(set(output_codes)) != len(output_codes):
        return None
    output_labels = list(
        map(
            lambda x: _generate_label(int(x)),
            tokens[2 + outputs_count : 2 + 2 * outputs_count],
        )
    )

    i = 2 + 2 * outputs_count
    gate_id = inputs_count
    while i < len(tokens):
        op = tokens[i]
        assert op in _gate_types.keys()
        label = _generate_label(gate_id)
        if op == 'NOT':
            assert i + 1 < len(tokens)
            operand = _generate_label(int(tokens[i + 1]))
            i += 2
            gate = Gate(label, NOT, (operand,))
        else:
            assert i + 2 < len(tokens)
            l_operand = _generate_label(int(tokens[i + 1]))
            r_operand = _generate_label(int(tokens[i + 2]))
            i += 3
            gate = Gate(label, _gate_types[op], (l_operand, r_operand))
        gate_id += 1
        gates[label] = gate

    used: tp.Set[Gate] = set()
    order: tp.List[Gate] = list()
    for gate in gates.values():
        _topology_sort(gate, used, gates, order)
    for gate in order:
        circuit.add_gate(gate)

    for label in output_labels:
        assert (
            label not in circuit.outputs
        ), f"\nCircuit: \n\t{circuit}\nString:\n\t{string}\nCodes: {output_codes}"
        circuit.mark_as_output(label)

    tt = circuit.get_truth_table()
    assert len(tt) == len(output_codes)
    for i, (table, code) in enumerate(zip(tt, output_codes)):
        table_num = int(''.join(map(lambda x: str(int(x)), reversed(table))), base=2)
        assert table_num == code, (
            f"\nCircuit: \n\t{circuit}\n"
            f"String:\n\t{string}\n"
            f"Codes: {output_codes}\n"
            f"Table num: {table_num} ({i})"
        )

    return circuit


def sort_outputs(circuit: Circuit) -> None:
    tt = circuit.get_truth_table()
    ordered_tt = list(enumerate(tt))
    ordered_tt.sort(key=lambda x: list(x[1]))
    new_outputs = [circuit.outputs[i[0]] for i in ordered_tt]
    circuit.order_outputs(new_outputs)


def txt_db_to_bin_db(txt_file: Path, bin_file: Path) -> None:
    with CircuitsDatabase() as db:
        with txt_file.open("r") as in_stream:
            for i, aig_string in enumerate(in_stream.readlines()):
                circuit = read_circuit_from_string(aig_string)
                if circuit is None:
                    continue
                sort_outputs(circuit)
                tt = circuit.get_truth_table()
                assert list(sorted(map(lambda x: list(x), tt))) == tt
                try:
                    db.add_circuit(circuit)
                except CircuitsDatabaseError:
                    pass
                    # print(f"Skipped: {aig_string}: {e}")
                if i > 0 and i % 10000 == 0:
                    print(f"Processed {i} circuits")
            print("Finished")
        with bin_file.open("wb") as out_stream:
            db.save(out_stream)


def _generate_label(identifier: int) -> Label:
    return f"gate_{identifier}"


def _topology_sort(
    gate: Gate, used: tp.Set[Gate], gates: tp.Dict[Label, Gate], order: tp.List[Gate]
):
    if gate in used:
        return
    used.add(gate)
    for operand in gate.operands:
        _topology_sort(gates[operand], used, gates, order)
    order.append(gate)


if __name__ == "__main__":
    # # AIG
    # txt_db_to_bin_db(
    #     Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db.txt"),
    #     Path("/home/vsevolod/sat/boolean-circuit-tool/aig_db_compressed.bin"),
    # )
    # exit(0)

    # # XAIG
    # txt_db_to_bin_db(
    #     Path("/home/vsevolod/sat/circuit_improvement_my/xaig_db_aig_str.txt"),
    #     Path("/home/vsevolod/sat/boolean-circuit-tool/xaig_db.bin"),
    # )
    # exit(0)

    # test
    random.seed(0)
    with CircuitsDatabase(
        "/home/vsevolod/sat/boolean-circuit-tool/aig_db_compressed.bin"
    ) as db:
        for i in range(10000000):
            if i % 1000 == 0:
                print(i)
            inputs = random.randint(2, 3)
            outputs = random.randint(1, 3)
            tt = [
                [random.choice([True, False]) for _ in range(1 << inputs)]
                for _ in range(outputs)
            ]
            if len(set(map(tuple, tt))) < len(tt):
                continue
            circuit = db.get_by_raw_truth_table(tt)
            assert circuit is not None
            assert circuit.get_truth_table() == tt
