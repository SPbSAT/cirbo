import pytest

from cirbo.core.circuit import Circuit
from cirbo.core.circuit.gate import AND, Gate, INPUT
from cirbo.core.exceptions import TruthTableNormalizationError
from cirbo.core.normalization import TruthTableNormalization
from cirbo.core.logic import DontCare

CONSTANT_FALSE = [False, False, False, False]
CONSTANT_TRUE = [True, True, True, True]
FIRST_INPUT = [False, False, True, True]
SECOND_INPUT = [False, True, False, True]
NOT_FIRST_INPUT = [True, True, False, False]
AND_OF_BOTH = [False, False, False, True]


def and_circuit() -> Circuit:
    """Two inputs and one AND gate over them, marked as the only output."""
    circuit = Circuit()
    circuit.add_gate(Gate("x0", INPUT))
    circuit.add_gate(Gate("x1", INPUT))
    circuit.add_gate(Gate("g", AND, ("x0", "x1")))
    circuit.set_outputs(["g"])
    return circuit


@pytest.mark.parametrize(
    "output, is_free",
    [
        (CONSTANT_FALSE, True),
        (CONSTANT_TRUE, True),
        (FIRST_INPUT, True),
        (SECOND_INPUT, True),
        (NOT_FIRST_INPUT, True),
        (AND_OF_BOTH, False),
        # Free once the unspecified row is read as the value making it an input.
        ([False, DontCare, True, True], True),
        ([DontCare, DontCare, DontCare, DontCare], True),
        # No completion of this one is a constant or an input.
        ([False, DontCare, True, False], False),
    ],
)
def test_free_outputs_are_deleted(output, is_free):
    normalization = TruthTableNormalization([output], reorder_outputs=False)

    assert normalization.all_outputs_are_free == is_free
    assert len(normalization.truth_table) == (0 if is_free else 1)


def test_outputs_that_need_a_gate_are_kept():
    normalization = TruthTableNormalization(
        [CONSTANT_FALSE, AND_OF_BOTH, NOT_FIRST_INPUT], reorder_outputs=False
    )

    assert list(normalization.truth_table) == [AND_OF_BOTH]
    assert not normalization.all_outputs_are_free


@pytest.mark.parametrize(
    "outputs",
    [
        [CONSTANT_FALSE, AND_OF_BOTH],
        [AND_OF_BOTH, CONSTANT_TRUE],
        [NOT_FIRST_INPUT, AND_OF_BOTH, SECOND_INPUT],
        [AND_OF_BOTH],
    ],
)
def test_denormalize_recovers_the_function_at_the_same_size(outputs):
    normalization = TruthTableNormalization(outputs, reorder_outputs=False)
    circuit = and_circuit()
    size = circuit.gates_number()

    denormalized = normalization.denormalize(circuit)

    assert [list(row) for row in denormalized.get_truth_table()] == outputs
    assert denormalized.gates_number() == size


def test_a_function_of_free_outputs_needs_no_circuit():
    normalization = TruthTableNormalization(
        [FIRST_INPUT, CONSTANT_TRUE], reorder_outputs=False
    )

    denormalized = normalization.free_circuit()

    assert denormalized.gates_number() == 0
    assert [list(row) for row in denormalized.get_truth_table()] == [
        FIRST_INPUT,
        CONSTANT_TRUE,
    ]


def test_all_four_steps_are_undone():
    # Two outputs start with 1 and so are negated, one of them becoming a constant and
    # the other an input; the two remaining ones are equal and out of order.
    outputs = [CONSTANT_TRUE, AND_OF_BOTH, NOT_FIRST_INPUT, AND_OF_BOTH]
    normalization = TruthTableNormalization(outputs)

    assert list(normalization.truth_table) == [AND_OF_BOTH]

    denormalized = normalization.denormalize(and_circuit())

    assert [list(row) for row in denormalized.get_truth_table()] == outputs
    assert denormalized.gates_number() == 1


def test_denormalize_rejects_a_circuit_over_other_inputs():
    normalization = TruthTableNormalization(
        [CONSTANT_FALSE, AND_OF_BOTH], reorder_outputs=False
    )
    circuit = Circuit()
    for label in ("x0", "x1", "x2"):
        circuit.add_gate(Gate(label, INPUT))
    circuit.add_gate(Gate("g", AND, ("x0", "x1")))
    circuit.set_outputs(["g"])

    with pytest.raises(TruthTableNormalizationError):
        normalization.denormalize(circuit)


def test_free_circuit_is_refused_when_an_output_needs_a_gate():
    normalization = TruthTableNormalization(
        [CONSTANT_FALSE, AND_OF_BOTH], reorder_outputs=False
    )

    with pytest.raises(TruthTableNormalizationError):
        normalization.free_circuit()


def test_outputs_containing_dont_care_cannot_be_reordered():
    with pytest.raises(TruthTableNormalizationError):
        TruthTableNormalization([[False, DontCare, True, False]])
