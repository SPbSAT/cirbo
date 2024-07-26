import typing as tp

from boolean_circuit_tool.cnf.utils import CnfRaw

from boolean_circuit_tool.core.circuit import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Circuit,
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


__all__ = ['Tseytin']


class Tseytin:
    """Class for converting circuits into CNF by Tseytin transformation."""

    def __init__(self, circuit: Circuit):
        self._circuit = circuit
        self._next_number = 1
        self._saved_lits = {}
        for input_label in self._circuit.inputs:
            self._generate_and_save_new_lit(input_label)

    def _generate_and_save_new_lit(self, label: str):
        index = self._next_number
        self._next_number += 1
        self._saved_lits[label] = index

    def _get_lit(self, label: str) -> int:
        if label not in self._saved_lits:
            self._generate_and_save_new_lit(label)
        return self._saved_lits[label]

    def to_cnf(self, outputs: tp.Optional[list[int]] = None) -> CnfRaw:
        """
        Makes Tseytin for outputs needed to be true.

        :param outputs: optional output indices which must be true. If it is None, indices are [0, 1,..., output_size-1].

        """
        if outputs is None:
            outputs = list(range(self._circuit.output_size))
        cnf: CnfRaw = []
        for output_index in outputs:
            lit = self._process_gate(self._circuit.output_at_index(output_index), cnf)
            cnf.append([lit])
        return cnf

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
        elif gate_type == NOT or gate_type == LNOT:
            cnf.append([lits[0], top_lit])
            cnf.append([-lits[0], -top_lit])
        elif gate_type == RNOT:
            cnf.append([lits[1], top_lit])
            cnf.append([-lits[1], -top_lit])
        elif gate_type == IFF or gate_type == LIFF:
            return lits[0]
        elif gate_type == RIFF:
            return lits[1]
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
        return top_lit
