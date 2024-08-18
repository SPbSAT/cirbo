import collections
import typing as tp

from cirbo.core.circuit import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Circuit,
    GateType,
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
from cirbo.sat.cnf.cnf import Cnf, CnfRaw, Lit


__all__ = ['tseytin_transformation']


def tseytin_transformation(
    circuit: Circuit,
    outputs: tp.Optional[list[int]] = None,
) -> Cnf:
    next_lit = 0

    def __register_new_gate() -> Lit:
        nonlocal next_lit
        next_lit += 1
        return next_lit

    saved_lits: dict[str, Lit] = collections.defaultdict(__register_new_gate)

    def get_lit(label: str) -> Lit:
        return saved_lits[label]

    for input_label in circuit.inputs:
        _ = saved_lits[input_label]

    if outputs is None:
        outputs = list(range(circuit.output_size))
    cnf: CnfRaw = []

    _operations: dict[GateType, tp.Callable[[CnfRaw, Lit, list[Lit]], None]] = {
        INPUT: _process_input,
        ALWAYS_TRUE: _process_always_true,
        ALWAYS_FALSE: _process_always_false,
        NOT: _process_not_or_lnot,
        LNOT: _process_not_or_lnot,
        RNOT: _process_rnot,
        IFF: _process_iff_or_liff,
        LIFF: _process_iff_or_liff,
        RIFF: _process_riff,
        AND: _process_and,
        NAND: _process_nand,
        OR: _process_or,
        NOR: _process_nor,
        XOR: _process_xor,
        NXOR: _process_nxor,
        GT: _process_gt,
        LT: _process_lt,
        GEQ: _process_geq,
        LEQ: _process_leq,
    }

    def process_gate(label: str) -> Lit:
        if label in saved_lits:
            return saved_lits[label]
        gate = circuit.get_gate(label)
        operands = gate.operands
        lits = [process_gate(lit) for lit in operands]
        gate_type = gate.gate_type
        top_lit = get_lit(label)
        _operations[gate_type](cnf, top_lit, lits)
        return top_lit

    for output_index in outputs:
        output_lit = process_gate(circuit.output_at_index(output_index))
        cnf.append([output_lit])
    return Cnf(cnf)


def _process_input(_: CnfRaw, __: Lit, ___: list[Lit]):
    pass


def _process_always_true(cnf: CnfRaw, top_lit: Lit, _: list[Lit]):
    cnf.append([top_lit])


def _process_always_false(cnf: CnfRaw, top_lit: Lit, _: list[Lit]):
    cnf.append([-top_lit])


def _process_not_or_lnot(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    cnf.append([lits[0], top_lit])
    cnf.append([-lits[0], -top_lit])


def _process_rnot(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    cnf.append([lits[1], top_lit])
    cnf.append([-lits[1], -top_lit])


def _process_iff_or_liff(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    cnf.append([lits[0], -top_lit])
    cnf.append([-lits[0], top_lit])


def _process_riff(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    cnf.append([lits[1], -top_lit])
    cnf.append([-lits[1], top_lit])


def _process_and(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    common = [top_lit]
    for lit in lits:
        common.append(-lit)
        cnf.append([lit, -top_lit])
    cnf.append(common)


def _process_nand(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    common = [-top_lit]
    for lit in lits:
        common.append(-lit)
        cnf.append([lit, top_lit])
    cnf.append(common)


def _process_or(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    common = [-top_lit]
    for lit in lits:
        common.append(lit)
        cnf.append([-lit, top_lit])
    cnf.append(common)


def _process_nor(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    common = [top_lit]
    for lit in lits:
        common.append(lit)
        cnf.append([-lit, -top_lit])
    cnf.append(common)


def _process_xor(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    a, b, c = lits[0], lits[1], top_lit
    cnf.append([-a, -b, -c])
    cnf.append([-a, b, c])
    cnf.append([a, -b, c])
    cnf.append([a, b, -c])


def _process_nxor(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    a, b, c = lits[0], lits[1], top_lit
    cnf.append([-a, -b, c])
    cnf.append([-a, b, -c])
    cnf.append([a, -b, -c])
    cnf.append([a, b, c])


def _process_gt(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    a, b, c = lits[0], lits[1], top_lit
    cnf.append([a, -c])
    cnf.append([-b, -c])
    cnf.append([-a, b, c])


def _process_lt(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    a, b, c = lits[0], lits[1], top_lit
    cnf.append([-a, -c])
    cnf.append([b, -c])
    cnf.append([a, -b, c])


def _process_geq(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    a, b, c = lits[0], lits[1], top_lit
    cnf.append([-a, c])
    cnf.append([b, c])
    cnf.append([a, -b, -c])


def _process_leq(cnf: CnfRaw, top_lit: Lit, lits: list[Lit]):
    a, b, c = lits[0], lits[1], top_lit
    cnf.append([a, c])
    cnf.append([-b, c])
    cnf.append([-a, b, -c])
