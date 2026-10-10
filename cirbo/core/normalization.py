"""Module defines normalization of the outputs of a boolean function."""

import typing as tp

from cirbo.core.boolean_function import RawTruthTable, RawTruthTableModel
from cirbo.core.circuit import Circuit
from cirbo.core.circuit.gate import ALWAYS_FALSE, ALWAYS_TRUE, Gate, INPUT, Label, NOT
from cirbo.core.exceptions import TruthTableNormalizationError
from cirbo.core.logic import DontCare, TriValue

__all__ = [
    'TruthTableNormalization',
    'is_normalized',
]


def is_normalized(truth_table: RawTruthTable) -> bool:
    """
    :param truth_table: the function, one row per output.
    :return: whether its outputs are already normalized, that is negated so that each
    starts with 0, sorted, free of duplicates, and none of them free.

    """
    outputs = [list(output) for output in truth_table]
    if not all(not output[0] for output in outputs):
        return False
    if not all(earlier < later for earlier, later in zip(outputs, outputs[1:])):
        return False
    input_size = (len(outputs[0]) - 1).bit_length()
    free = [candidate.values(input_size) for candidate in _free_outputs(input_size)]
    return all(output not in free for output in outputs)


class _FreeOutput(tp.NamedTuple):
    """
    A function an output may compute without a gate of its own.

    `input_index` is None for the two constants, otherwise the output is that input,
    negated when `negated` is set.

    """

    input_index: tp.Optional[int]
    negated: bool

    def values(self, input_size: int) -> tp.List[bool]:
        """
        :param input_size: number of inputs of the function.
        :return: truth table of this function over `input_size` inputs.

        """
        rows = 1 << input_size
        if self.input_index is None:
            return [self.negated] * rows
        shift = input_size - 1 - self.input_index
        return [bool((row >> shift) & 1) != self.negated for row in range(rows)]


def _free_outputs(input_size: int) -> tp.List[_FreeOutput]:
    """
    :param input_size: number of inputs of the function.
    :return: every function an output may compute without a gate: the two constants,
    the inputs, and their negations. Ordered so that an output that may be several of
    them is always resolved to the same one.

    """
    return (
        [_FreeOutput(None, False), _FreeOutput(None, True)]
        + [_FreeOutput(index, False) for index in range(input_size)]
        + [_FreeOutput(index, True) for index in range(input_size)]
    )


class TruthTableNormalization:
    """
    Normalization of the outputs of a boolean function, and the way to undo it.

    Four steps, none of which changes the size of a smallest circuit:

    1. negate every output whose truth table starts with 1;
    2. sort the outputs;
    3. delete duplicate outputs;
    4. delete the free outputs, which are the constants and the inputs, negated or
       not. `Circuit.gates_number` counts none of `INPUT`, `NOT`, `IFF`,
       `ALWAYS_FALSE` and `ALWAYS_TRUE`, so such an output is carried at no cost.

    `truth_table` is the function that is left. `denormalize` takes a circuit computing
    it and returns a circuit computing the original function, of the same size.

    """

    def __init__(
        self,
        truth_table: RawTruthTableModel,
        *,
        reorder_outputs: bool = True,
    ):
        """
        :param truth_table: the function, one row per output. Rows may contain
        `DontCare` only when `reorder_outputs` is False, since the order and the
        polarity of an output are not defined until its values are.
        :param reorder_outputs: whether to apply steps 1 to 3.

        """
        if len(truth_table) == 0:
            raise TruthTableNormalizationError("Truth table has no outputs")
        self.input_size = (len(truth_table[0]) - 1).bit_length()
        if 1 << self.input_size != len(truth_table[0]):
            raise TruthTableNormalizationError(
                f"Truth table of length {len(truth_table[0])} is not a power of two"
            )

        self.negations: tp.Optional[tp.List[bool]] = None
        self.permutation: tp.Optional[tp.List[int]] = None
        self.mapping: tp.Optional[tp.List[int]] = None
        self.free: tp.List[tp.Optional[_FreeOutput]] = []

        table = truth_table
        if reorder_outputs:
            if any(value is DontCare for output in table for value in output):
                raise TruthTableNormalizationError(
                    "Cannot apply steps 1 to 3 to a function containing DontCare: "
                    "which output is negated is decided by its first value, and the "
                    "order of two outputs by the first value they differ at"
                )
            table = self._negate_outputs(table)
            table = self._sort_outputs(table)
            table = self._delete_duplicate_outputs(table)
        self.truth_table = self._delete_free_outputs(table)

    @property
    def all_outputs_are_free(self) -> bool:
        """
        :return: whether step 4 deleted every output, so that the function needs no gate
        at all and `free_circuit` answers it without a circuit to start from.

        """
        return len(self.truth_table) == 0

    def denormalize(self, circuit: Circuit) -> Circuit:
        """
        Undo the normalization on a circuit computing `truth_table`.

        :param circuit: circuit computing `truth_table`.
        :return: circuit computing the function this was constructed from. Its gates
        are the gates of `circuit`: what is added here is not counted by
        `Circuit.gates_number`.

        """
        return self._denormalize(circuit, None)

    def free_circuit(
        self, input_labels: tp.Optional[tp.Sequence[Label]] = None
    ) -> Circuit:
        """
        Build the circuit of a function every output of which is free.

        :param input_labels: labels for its inputs. Defaults to `x0`, `x1` and so on.
        :return: gateless circuit computing the function this was constructed from.

        """
        if not self.all_outputs_are_free:
            raise TruthTableNormalizationError(
                f"{len(self.truth_table)} output(s) need a gate, so a circuit "
                f"computing them is required"
            )
        return self._denormalize(None, input_labels)

    def _denormalize(
        self,
        circuit: tp.Optional[Circuit],
        input_labels: tp.Optional[tp.Sequence[Label]],
    ) -> Circuit:
        circuit = self._restore_free_outputs(circuit, input_labels)
        if self.mapping is not None:
            self._undo_outputs_deletion(circuit)
        if self.permutation is not None:
            self._unsort_outputs(circuit)
        if self.negations is not None:
            self._denormalize_outputs(circuit)
        return circuit

    def _negate_outputs(self, truth_table: RawTruthTableModel) -> RawTruthTableModel:
        negated: tp.List[tp.MutableSequence[TriValue]] = []
        negations = []
        for output in truth_table:
            negations.append(bool(output[0]))
            flipped: tp.List[TriValue] = [not value for value in output]
            negated.append(flipped if output[0] else output)
        self.negations = negations
        return negated

    def _sort_outputs(self, truth_table: RawTruthTableModel) -> RawTruthTableModel:
        ordered = sorted(enumerate(truth_table), key=lambda pair: list(pair[1]))
        self.permutation = [index for index, _ in ordered]
        return [output for _, output in ordered]

    def _delete_duplicate_outputs(
        self, truth_table: RawTruthTableModel
    ) -> RawTruthTableModel:
        # Assumes outputs are sorted, so duplicates are adjacent.
        kept = [truth_table[0]]
        mapping = [0]
        for index in range(1, len(truth_table)):
            if truth_table[index] != truth_table[index - 1]:
                kept.append(truth_table[index])
            mapping.append(len(kept) - 1)
        self.mapping = mapping
        return kept

    def _delete_free_outputs(
        self, truth_table: RawTruthTableModel
    ) -> RawTruthTableModel:
        kept = []
        for output in truth_table:
            free = self._free_form(output)
            self.free.append(free)
            if free is None:
                kept.append(output)
        return kept

    def _free_form(self, output: tp.Sequence) -> tp.Optional[_FreeOutput]:
        # An output containing DontCare is free when some completion of it is, which is
        # decided row by row: a free output is carried on its own and shares no gate
        # with the rest, so making one free never costs another one anything.
        for candidate in _free_outputs(self.input_size):
            values = candidate.values(self.input_size)
            if all(
                value is DontCare or bool(value) == expected
                for value, expected in zip(output, values)
            ):
                return candidate
        return None

    def _restore_free_outputs(
        self,
        circuit: tp.Optional[Circuit],
        input_labels: tp.Optional[tp.Sequence[Label]],
    ) -> Circuit:
        if circuit is None:
            labels = (
                list(input_labels)
                if input_labels is not None
                else [f"x{index}" for index in range(self.input_size)]
            )
            if len(labels) != self.input_size:
                raise TruthTableNormalizationError(
                    f"Got {len(labels)} input labels for {self.input_size} inputs"
                )
            circuit = Circuit()
            for label in labels:
                circuit.add_gate(Gate(label, INPUT))

        inputs = list(circuit.inputs)
        if len(inputs) != self.input_size:
            raise TruthTableNormalizationError(
                f"Circuit has {len(inputs)} inputs, the function has {self.input_size}"
            )
        if len(circuit.outputs) != len(self.truth_table):
            raise TruthTableNormalizationError(
                f"Circuit has {len(circuit.outputs)} outputs, the normalized function "
                f"has {len(self.truth_table)}"
            )
        built = iter(circuit.outputs)
        circuit.set_outputs(
            [
                next(built) if free is None else _carry(circuit, free, inputs)
                for free in self.free
            ]
        )
        return circuit

    def _undo_outputs_deletion(self, circuit: Circuit) -> None:
        if self.mapping is None:
            raise TruthTableNormalizationError("Normalization was not applied")
        circuit._outputs = [circuit.outputs[index] for index in self.mapping]

    def _unsort_outputs(self, circuit: Circuit) -> None:
        if self.permutation is None:
            raise TruthTableNormalizationError("Normalization was not applied")
        if len(self.permutation) != len(circuit.outputs):
            raise TruthTableNormalizationError(
                f"Circuit has {len(circuit.outputs)} outputs, the normalization has "
                f"{len(self.negations or self.permutation or [])}"
            )
        unsorted_outputs = ['' for _ in circuit.outputs]
        for sorted_index, original_index in enumerate(self.permutation):
            unsorted_outputs[original_index] = circuit.outputs[sorted_index]
        circuit.order_outputs(unsorted_outputs)

    def _denormalize_outputs(self, circuit: Circuit) -> None:
        if self.negations is None:
            raise TruthTableNormalizationError("Normalization was not applied")
        if len(circuit.outputs) != len(self.negations):
            raise TruthTableNormalizationError(
                f"Circuit has {len(circuit.outputs)} outputs, the normalization has "
                f"{len(self.negations or self.permutation or [])}"
            )
        circuit._outputs = [
            _negate_gate(circuit, output) if negation else output
            for output, negation in zip(circuit.outputs, self.negations)
        ]


def _carry(circuit: Circuit, free: _FreeOutput, inputs: tp.Sequence[Label]) -> Label:
    """
    :return: label of the gate carrying `free` as an output, adding it to `circuit` if
    it is not there yet.

    """
    if free.input_index is None:
        label = "always_true" if free.negated else "always_false"
        if not circuit.has_gate(label):
            circuit.emplace_gate(label, ALWAYS_TRUE if free.negated else ALWAYS_FALSE)
        return label
    source = inputs[free.input_index]
    return _negate_gate(circuit, source) if free.negated else source


def _negate_gate(circuit: Circuit, gate: Label) -> Label:
    not_gate = f"not_{gate}"
    if not_gate not in circuit.gates.keys():
        circuit.emplace_gate(not_gate, NOT, (gate,))
    return not_gate
