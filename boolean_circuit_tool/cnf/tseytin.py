from boolean_circuit_tool.core.circuit import (
    Circuit,
    AND,
    OR,
    XOR,
    NOT,
    NAND,
    NOR,
    NXOR,
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    INPUT,
    GT,
    GEQ,
    LT,
    LEQ,
    IFF,
)
from boolean_circuit_tool.cnf.cnf import CnfRaw


def circuit_to_cnf(circuit: Circuit) -> CnfRaw:
    pass


class Tseytin:
    def __init__(self, circuit: Circuit):
        self._circuit = circuit
        self._next_number = 1
        self._saved_lits = {}

    def _generate_and_save_new_lit(self, label: str):
        index = self._next_number
        self._next_number += 1
        self._saved_lits[label] = index

    def _get_lit(self, label: str) -> int:
        if label  not in self._saved_lits:
            self._generate_and_save_new_lit(label)
        return self._saved_lits[label]

    def to_cnf(self) -> CnfRaw:
        for input_label in self._circuit.inputs:
            self._generate_and_save_new_lit(input_label)
        outs = self._circuit.outputs
        a = self._circuit.output_at_index(0)

    def _out_to_cnf(self) -> CnfRaw:
        pass

    def _process_gate(self, label: str, cnf: CnfRaw) -> int:
        gate = self._circuit.get_element(label)
        operands = gate.operands
        lits = [self._process_gate(l, cnf) for l in operands]
        gate_type = gate.gate_type
        top_lit = self._get_lit(label)
        if gate_type == INPUT:
            pass
        elif gate_type == ALWAYS_TRUE:
            cnf.append([top_lit])
        elif gate_type == ALWAYS_FALSE:
            cnf.append([-top_lit])
        elif gate_type == NOT:
            cnf.append([lits[0], top_lit])
            cnf.append([-lits[0], -top_lit])
        elif gate_type == AND:
            common = [top_lit]
            for lit in lits:
                common.append(-lit)
                cnf.append([lit, -top_lit])
            cnf.append(common)
        elif gate_type == NAND:
            common = [-top_lit]
            for lit in lits:
                common.append(-lit)
                cnf.append([lit, top_lit])
            cnf.append(common)
        elif gate_type == OR:
            common = [-top_lit]
            for lit in lits:
                common.append(lit)
                cnf.append([-lit, top_lit])
            cnf.append(common)
        elif gate_type == NOR:
            common = [top_lit]
            for lit in lits:
                common.append(lit)
                cnf.append([-lit, -top_lit])
            cnf.append(common)
        elif gate_type == IFF:
            a, b, c, d = tuple(lits[:3] + [top_lit])
            cnf.append([a, c, -d])
            cnf.append([a, -c, d])
            cnf.append([-a, b, -d])
            cnf.append([-a, -b, d])
        else:
            a, b, c = lits[0], lits[1], top_lit
            if gate_type == XOR:
                a, b, c = lits[0], lits[1], top_lit
                cnf.append([-a, -b, -c])
                cnf.append([-a, b, c])
                cnf.append([a, -b, c])
                cnf.append([a, b, -c])
            elif gate_type == NXOR:
                cnf.append([-a, -b, c])
                cnf.append([-a, b, -c])
                cnf.append([a, -b, -c])
                cnf.append([a, b, c])
            elif gate_type == AND:
                cnf.append([a, -c])
                cnf.append([b, -c])
                cnf.append([-a, -b, c])
            elif gate_type == OR:
                cnf.append([-a, c])
                cnf.append([-b, c])
                cnf.append([a, b, -c])
            elif gate_type == GT:
                cnf.append([a, -c])
                cnf.append([-b, -c])
                cnf.append([-a, b, c])
            elif gate_type == LT:
                cnf.append([-a, -c])
                cnf.append([b, -c])
                cnf.append([a, -b, c])
            elif gate_type == GEQ:
                cnf.append([-a, c])
                cnf.append([b, c])
                cnf.append([a, -b, -c])
            elif gate_type == LEQ:
                cnf.append([a, c])
                cnf.append([-b, c])
                cnf.append([-a, b, -c])

