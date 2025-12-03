import pytest

from cirbo.core.circuit import Circuit, Gate, gate
from cirbo.minimization.simplification import RemoveConstantGates


# =============================================================================
# Test cases for unary gates with constant operands
# =============================================================================

# Test: NOT(ALWAYS_TRUE) -> ALWAYS_FALSE
unary_not_true = Circuit()
unary_not_true.add_gate(Gate('input1', gate.INPUT))
unary_not_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
unary_not_true.emplace_gate('not_const', gate.NOT, ('const',))
unary_not_true.set_outputs(['not_const'])

expected_unary_not_true = Circuit()
expected_unary_not_true.add_gate(Gate('input1', gate.INPUT))
expected_unary_not_true.emplace_gate('not_const', gate.ALWAYS_FALSE, ())
expected_unary_not_true.set_outputs(['not_const'])


# Test: NOT(ALWAYS_FALSE) -> ALWAYS_TRUE
unary_not_false = Circuit()
unary_not_false.add_gate(Gate('input1', gate.INPUT))
unary_not_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
unary_not_false.emplace_gate('not_const', gate.NOT, ('const',))
unary_not_false.set_outputs(['not_const'])

expected_unary_not_false = Circuit()
expected_unary_not_false.add_gate(Gate('input1', gate.INPUT))
expected_unary_not_false.emplace_gate('not_const', gate.ALWAYS_TRUE, ())
expected_unary_not_false.set_outputs(['not_const'])


# Test: IFF(ALWAYS_TRUE) -> ALWAYS_TRUE
unary_iff_true = Circuit()
unary_iff_true.add_gate(Gate('input1', gate.INPUT))
unary_iff_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
unary_iff_true.emplace_gate('iff_const', gate.IFF, ('const',))
unary_iff_true.set_outputs(['iff_const'])

expected_unary_iff_true = Circuit()
expected_unary_iff_true.add_gate(Gate('input1', gate.INPUT))
expected_unary_iff_true.emplace_gate('iff_const', gate.ALWAYS_TRUE, ())
expected_unary_iff_true.set_outputs(['iff_const'])


# Test: IFF(ALWAYS_FALSE) -> ALWAYS_FALSE
unary_iff_false = Circuit()
unary_iff_false.add_gate(Gate('input1', gate.INPUT))
unary_iff_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
unary_iff_false.emplace_gate('iff_const', gate.IFF, ('const',))
unary_iff_false.set_outputs(['iff_const'])

expected_unary_iff_false = Circuit()
expected_unary_iff_false.add_gate(Gate('input1', gate.INPUT))
expected_unary_iff_false.emplace_gate('iff_const', gate.ALWAYS_FALSE, ())
expected_unary_iff_false.set_outputs(['iff_const'])


# =============================================================================
# Test cases for AND gate with constant operands
# =============================================================================

# Test: AND(x, ALWAYS_TRUE) -> x
and_with_true_right = Circuit()
and_with_true_right.add_inputs(['x'])
and_with_true_right.emplace_gate('const', gate.ALWAYS_TRUE, ())
and_with_true_right.emplace_gate('result', gate.AND, ('x', 'const'))
and_with_true_right.set_outputs(['result'])

expected_and_with_true_right = Circuit()
expected_and_with_true_right.add_inputs(['x'])
expected_and_with_true_right.set_outputs(['x'])


# Test: AND(ALWAYS_TRUE, x) -> x
and_with_true_left = Circuit()
and_with_true_left.add_inputs(['x'])
and_with_true_left.emplace_gate('const', gate.ALWAYS_TRUE, ())
and_with_true_left.emplace_gate('result', gate.AND, ('const', 'x'))
and_with_true_left.set_outputs(['result'])

expected_and_with_true_left = Circuit()
expected_and_with_true_left.add_inputs(['x'])
expected_and_with_true_left.set_outputs(['x'])


# Test: AND(x, ALWAYS_FALSE) -> ALWAYS_FALSE
and_with_false_right = Circuit()
and_with_false_right.add_inputs(['x'])
and_with_false_right.emplace_gate('const', gate.ALWAYS_FALSE, ())
and_with_false_right.emplace_gate('result', gate.AND, ('x', 'const'))
and_with_false_right.set_outputs(['result'])

expected_and_with_false_right = Circuit()
expected_and_with_false_right.add_inputs(['x'])
expected_and_with_false_right.emplace_gate('result', gate.ALWAYS_FALSE, ())
expected_and_with_false_right.set_outputs(['result'])


# Test: AND(ALWAYS_FALSE, x) -> ALWAYS_FALSE
and_with_false_left = Circuit()
and_with_false_left.add_inputs(['x'])
and_with_false_left.emplace_gate('const', gate.ALWAYS_FALSE, ())
and_with_false_left.emplace_gate('result', gate.AND, ('const', 'x'))
and_with_false_left.set_outputs(['result'])

expected_and_with_false_left = Circuit()
expected_and_with_false_left.add_inputs(['x'])
expected_and_with_false_left.emplace_gate('result', gate.ALWAYS_FALSE, ())
expected_and_with_false_left.set_outputs(['result'])


# =============================================================================
# Test cases for OR gate with constant operands
# =============================================================================

# Test: OR(x, ALWAYS_TRUE) -> ALWAYS_TRUE
or_with_true_right = Circuit()
or_with_true_right.add_inputs(['x'])
or_with_true_right.emplace_gate('const', gate.ALWAYS_TRUE, ())
or_with_true_right.emplace_gate('result', gate.OR, ('x', 'const'))
or_with_true_right.set_outputs(['result'])

expected_or_with_true_right = Circuit()
expected_or_with_true_right.add_inputs(['x'])
expected_or_with_true_right.emplace_gate('result', gate.ALWAYS_TRUE, ())
expected_or_with_true_right.set_outputs(['result'])


# Test: OR(x, ALWAYS_FALSE) -> x
or_with_false_right = Circuit()
or_with_false_right.add_inputs(['x'])
or_with_false_right.emplace_gate('const', gate.ALWAYS_FALSE, ())
or_with_false_right.emplace_gate('result', gate.OR, ('x', 'const'))
or_with_false_right.set_outputs(['result'])

expected_or_with_false_right = Circuit()
expected_or_with_false_right.add_inputs(['x'])
expected_or_with_false_right.set_outputs(['x'])


# =============================================================================
# Test cases for XOR gate with constant operands
# =============================================================================

# Test: XOR(x, ALWAYS_TRUE) -> NOT(x)
xor_with_true = Circuit()
xor_with_true.add_inputs(['x'])
xor_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
xor_with_true.emplace_gate('result', gate.XOR, ('x', 'const'))
xor_with_true.set_outputs(['result'])

expected_xor_with_true = Circuit()
expected_xor_with_true.add_inputs(['x'])
expected_xor_with_true.emplace_gate('result', gate.NOT, ('x',))
expected_xor_with_true.set_outputs(['result'])


# Test: XOR(x, ALWAYS_FALSE) -> x
xor_with_false = Circuit()
xor_with_false.add_inputs(['x'])
xor_with_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
xor_with_false.emplace_gate('result', gate.XOR, ('x', 'const'))
xor_with_false.set_outputs(['result'])

expected_xor_with_false = Circuit()
expected_xor_with_false.add_inputs(['x'])
expected_xor_with_false.set_outputs(['x'])


# =============================================================================
# Test cases for NAND gate with constant operands
# =============================================================================

# Test: NAND(x, ALWAYS_TRUE) -> NOT(x)
nand_with_true = Circuit()
nand_with_true.add_inputs(['x'])
nand_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
nand_with_true.emplace_gate('result', gate.NAND, ('x', 'const'))
nand_with_true.set_outputs(['result'])

expected_nand_with_true = Circuit()
expected_nand_with_true.add_inputs(['x'])
expected_nand_with_true.emplace_gate('result', gate.NOT, ('x',))
expected_nand_with_true.set_outputs(['result'])


# Test: NAND(x, ALWAYS_FALSE) -> ALWAYS_TRUE
nand_with_false = Circuit()
nand_with_false.add_inputs(['x'])
nand_with_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
nand_with_false.emplace_gate('result', gate.NAND, ('x', 'const'))
nand_with_false.set_outputs(['result'])

expected_nand_with_false = Circuit()
expected_nand_with_false.add_inputs(['x'])
expected_nand_with_false.emplace_gate('result', gate.ALWAYS_TRUE, ())
expected_nand_with_false.set_outputs(['result'])


# =============================================================================
# Test cases for NOR gate with constant operands
# =============================================================================

# Test: NOR(x, ALWAYS_TRUE) -> ALWAYS_FALSE
nor_with_true = Circuit()
nor_with_true.add_inputs(['x'])
nor_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
nor_with_true.emplace_gate('result', gate.NOR, ('x', 'const'))
nor_with_true.set_outputs(['result'])

expected_nor_with_true = Circuit()
expected_nor_with_true.add_inputs(['x'])
expected_nor_with_true.emplace_gate('result', gate.ALWAYS_FALSE, ())
expected_nor_with_true.set_outputs(['result'])


# Test: NOR(x, ALWAYS_FALSE) -> NOT(x)
nor_with_false = Circuit()
nor_with_false.add_inputs(['x'])
nor_with_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
nor_with_false.emplace_gate('result', gate.NOR, ('x', 'const'))
nor_with_false.set_outputs(['result'])

expected_nor_with_false = Circuit()
expected_nor_with_false.add_inputs(['x'])
expected_nor_with_false.emplace_gate('result', gate.NOT, ('x',))
expected_nor_with_false.set_outputs(['result'])


# =============================================================================
# Test cases for NXOR gate with constant operands
# =============================================================================

# Test: NXOR(x, ALWAYS_TRUE) -> x (since NXOR(x, 1) = NOT(XOR(x, 1)) = NOT(NOT(x)) = x)
nxor_with_true = Circuit()
nxor_with_true.add_inputs(['x'])
nxor_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
nxor_with_true.emplace_gate('result', gate.NXOR, ('x', 'const'))
nxor_with_true.set_outputs(['result'])

expected_nxor_with_true = Circuit()
expected_nxor_with_true.add_inputs(['x'])
expected_nxor_with_true.set_outputs(['x'])


# Test: NXOR(x, ALWAYS_FALSE) -> NOT(x) (since NXOR(x, 0) = NOT(XOR(x, 0)) = NOT(x))
nxor_with_false = Circuit()
nxor_with_false.add_inputs(['x'])
nxor_with_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
nxor_with_false.emplace_gate('result', gate.NXOR, ('x', 'const'))
nxor_with_false.set_outputs(['result'])

expected_nxor_with_false = Circuit()
expected_nxor_with_false.add_inputs(['x'])
expected_nxor_with_false.emplace_gate('result', gate.NOT, ('x',))
expected_nxor_with_false.set_outputs(['result'])


# =============================================================================
# Test cases for comparison gates (GT, LT, GEQ, LEQ) with constant operands
# =============================================================================

# Test: GT(x, ALWAYS_FALSE) -> x (since x > 0 is true only when x is 1)
gt_with_false = Circuit()
gt_with_false.add_inputs(['x'])
gt_with_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
gt_with_false.emplace_gate('result', gate.GT, ('x', 'const'))
gt_with_false.set_outputs(['result'])

expected_gt_with_false = Circuit()
expected_gt_with_false.add_inputs(['x'])
expected_gt_with_false.set_outputs(['x'])


# Test: GT(x, ALWAYS_TRUE) -> ALWAYS_FALSE (since x can't be greater than 1)
gt_with_true = Circuit()
gt_with_true.add_inputs(['x'])
gt_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
gt_with_true.emplace_gate('result', gate.GT, ('x', 'const'))
gt_with_true.set_outputs(['result'])

expected_gt_with_true = Circuit()
expected_gt_with_true.add_inputs(['x'])
expected_gt_with_true.emplace_gate('result', gate.ALWAYS_FALSE, ())
expected_gt_with_true.set_outputs(['result'])


# Test: LT(x, ALWAYS_TRUE) -> NOT(x) (since x < 1 is true only when x is 0)
lt_with_true = Circuit()
lt_with_true.add_inputs(['x'])
lt_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
lt_with_true.emplace_gate('result', gate.LT, ('x', 'const'))
lt_with_true.set_outputs(['result'])

expected_lt_with_true = Circuit()
expected_lt_with_true.add_inputs(['x'])
expected_lt_with_true.emplace_gate('result', gate.NOT, ('x',))
expected_lt_with_true.set_outputs(['result'])


# Test: GEQ(x, ALWAYS_FALSE) -> ALWAYS_TRUE (since x >= 0 is always true)
geq_with_false = Circuit()
geq_with_false.add_inputs(['x'])
geq_with_false.emplace_gate('const', gate.ALWAYS_FALSE, ())
geq_with_false.emplace_gate('result', gate.GEQ, ('x', 'const'))
geq_with_false.set_outputs(['result'])

expected_geq_with_false = Circuit()
expected_geq_with_false.add_inputs(['x'])
expected_geq_with_false.emplace_gate('result', gate.ALWAYS_TRUE, ())
expected_geq_with_false.set_outputs(['result'])


# Test: LEQ(x, ALWAYS_TRUE) -> ALWAYS_TRUE (since x <= 1 is always true)
leq_with_true = Circuit()
leq_with_true.add_inputs(['x'])
leq_with_true.emplace_gate('const', gate.ALWAYS_TRUE, ())
leq_with_true.emplace_gate('result', gate.LEQ, ('x', 'const'))
leq_with_true.set_outputs(['result'])

expected_leq_with_true = Circuit()
expected_leq_with_true.add_inputs(['x'])
expected_leq_with_true.emplace_gate('result', gate.ALWAYS_TRUE, ())
expected_leq_with_true.set_outputs(['result'])


# =============================================================================
# Test cases for both operands being constants
# =============================================================================

# Test: AND(ALWAYS_TRUE, ALWAYS_TRUE) -> ALWAYS_TRUE
and_both_true = Circuit()
and_both_true.add_inputs(['x'])
and_both_true.emplace_gate('const1', gate.ALWAYS_TRUE, ())
and_both_true.emplace_gate('const2', gate.ALWAYS_TRUE, ())
and_both_true.emplace_gate('result', gate.AND, ('const1', 'const2'))
and_both_true.set_outputs(['result'])

expected_and_both_true = Circuit()
expected_and_both_true.add_inputs(['x'])
expected_and_both_true.emplace_gate('result', gate.ALWAYS_TRUE, ())
expected_and_both_true.set_outputs(['result'])


# Test: AND(ALWAYS_TRUE, ALWAYS_FALSE) -> ALWAYS_FALSE
and_true_false = Circuit()
and_true_false.add_inputs(['x'])
and_true_false.emplace_gate('const1', gate.ALWAYS_TRUE, ())
and_true_false.emplace_gate('const2', gate.ALWAYS_FALSE, ())
and_true_false.emplace_gate('result', gate.AND, ('const1', 'const2'))
and_true_false.set_outputs(['result'])

expected_and_true_false = Circuit()
expected_and_true_false.add_inputs(['x'])
expected_and_true_false.emplace_gate('result', gate.ALWAYS_FALSE, ())
expected_and_true_false.set_outputs(['result'])


# Test: OR(ALWAYS_FALSE, ALWAYS_FALSE) -> ALWAYS_FALSE
or_both_false = Circuit()
or_both_false.add_inputs(['x'])
or_both_false.emplace_gate('const1', gate.ALWAYS_FALSE, ())
or_both_false.emplace_gate('const2', gate.ALWAYS_FALSE, ())
or_both_false.emplace_gate('result', gate.OR, ('const1', 'const2'))
or_both_false.set_outputs(['result'])

expected_or_both_false = Circuit()
expected_or_both_false.add_inputs(['x'])
expected_or_both_false.emplace_gate('result', gate.ALWAYS_FALSE, ())
expected_or_both_false.set_outputs(['result'])


# =============================================================================
# Test cases for constant propagation through multiple layers
# =============================================================================

# Test: Constant propagates through multiple gates
# x -> AND(x, TRUE) -> AND(result, FALSE) -> final
propagation_chain = Circuit()
propagation_chain.add_inputs(['x'])
propagation_chain.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
propagation_chain.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
propagation_chain.emplace_gate('intermediate', gate.AND, ('x', 'true_const'))
propagation_chain.emplace_gate('final', gate.AND, ('intermediate', 'false_const'))
propagation_chain.set_outputs(['final'])

expected_propagation_chain = Circuit()
expected_propagation_chain.add_inputs(['x'])
expected_propagation_chain.emplace_gate('final', gate.ALWAYS_FALSE, ())
expected_propagation_chain.set_outputs(['final'])


# Test: Complex propagation with multiple paths
# Creates a diamond pattern where constants propagate through different paths
complex_propagation = Circuit()
complex_propagation.add_inputs(['x', 'y'])
complex_propagation.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
complex_propagation.emplace_gate('left', gate.AND, ('x', 'true_const'))  # -> x
complex_propagation.emplace_gate('right', gate.OR, ('y', 'true_const'))  # -> TRUE
complex_propagation.emplace_gate(
    'final', gate.AND, ('left', 'right')
)  # -> AND(x, TRUE) -> x
complex_propagation.set_outputs(['final'])

expected_complex_propagation = Circuit()
expected_complex_propagation.add_inputs(['x', 'y'])
expected_complex_propagation.set_outputs(['x'])


# =============================================================================
# Test cases for circuits without constants (should remain unchanged)
# =============================================================================

no_constants = Circuit()
no_constants.add_inputs(['x', 'y'])
no_constants.emplace_gate('and1', gate.AND, ('x', 'y'))
no_constants.emplace_gate('or1', gate.OR, ('x', 'y'))
no_constants.emplace_gate('xor1', gate.XOR, ('and1', 'or1'))
no_constants.set_outputs(['xor1'])

expected_no_constants = Circuit()
expected_no_constants.add_inputs(['x', 'y'])
expected_no_constants.emplace_gate('and1', gate.AND, ('x', 'y'))
expected_no_constants.emplace_gate('or1', gate.OR, ('x', 'y'))
expected_no_constants.emplace_gate('xor1', gate.XOR, ('and1', 'or1'))
expected_no_constants.set_outputs(['xor1'])


# =============================================================================
# Test cases for edge cases
# =============================================================================

# Test: Constant gate is the direct output
const_output = Circuit()
const_output.add_inputs(['x'])
const_output.emplace_gate('out', gate.ALWAYS_TRUE, ())
const_output.set_outputs(['out'])

expected_const_output = Circuit()
expected_const_output.add_inputs(['x'])
expected_const_output.emplace_gate('out', gate.ALWAYS_TRUE, ())
expected_const_output.set_outputs(['out'])


# Test: Multiple outputs, some become constants
multi_output = Circuit()
multi_output.add_inputs(['x'])
multi_output.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
multi_output.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
multi_output.emplace_gate('out1', gate.AND, ('x', 'true_const'))  # -> x
multi_output.emplace_gate('out2', gate.AND, ('x', 'false_const'))  # -> FALSE
multi_output.set_outputs(['out1', 'out2'])

expected_multi_output = Circuit()
expected_multi_output.add_inputs(['x'])
expected_multi_output.emplace_gate('out2', gate.ALWAYS_FALSE, ())
expected_multi_output.set_outputs(['x', 'out2'])


# Test: Duplicate outputs after remapping
duplicate_output = Circuit()
duplicate_output.add_inputs(['x'])
duplicate_output.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
duplicate_output.emplace_gate('out1', gate.AND, ('x', 'true_const'))
duplicate_output.emplace_gate('out2', gate.OR, ('x', 'true_const'))
duplicate_output.set_outputs(['out1', 'out2'])

expected_duplicate_output = Circuit()
expected_duplicate_output.add_inputs(['x'])
expected_duplicate_output.emplace_gate('out2', gate.ALWAYS_TRUE, ())
expected_duplicate_output.set_outputs(['x', 'out2'])


# Test: Idempotency - applying twice should give same result
idempotency_test = Circuit()
idempotency_test.add_inputs(['x', 'y'])
idempotency_test.emplace_gate('c1', gate.ALWAYS_TRUE, ())
idempotency_test.emplace_gate('c2', gate.ALWAYS_FALSE, ())
idempotency_test.emplace_gate('g1', gate.AND, ('x', 'c1'))
idempotency_test.emplace_gate('g2', gate.OR, ('y', 'c2'))
idempotency_test.emplace_gate('out', gate.XOR, ('g1', 'g2'))
idempotency_test.set_outputs(['out'])


# =============================================================================
# Test cases for deep chain propagation (3+ levels)
# =============================================================================

# Test: Deep chain - constant propagates through 4 levels
# TRUE -> AND(x, TRUE) -> OR(result, FALSE) -> XOR(result, FALSE) -> NOT(result)
deep_chain = Circuit()
deep_chain.add_inputs(['x'])
deep_chain.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
deep_chain.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
deep_chain.emplace_gate('level1', gate.AND, ('x', 'true_const'))  # -> x
deep_chain.emplace_gate('level2', gate.OR, ('level1', 'false_const'))  # -> x
deep_chain.emplace_gate('level3', gate.XOR, ('level2', 'false_const'))  # -> x
deep_chain.emplace_gate('level4', gate.NOT, ('level3',))  # -> NOT(x)
deep_chain.set_outputs(['level4'])

expected_deep_chain = Circuit()
expected_deep_chain.add_inputs(['x'])
expected_deep_chain.emplace_gate('level4', gate.NOT, ('x',))
expected_deep_chain.set_outputs(['level4'])


# Test: Chain where intermediate result becomes constant
# x -> AND(x, FALSE) -> OR(result, TRUE) -> output
# AND(x, FALSE) = FALSE, OR(FALSE, TRUE) = TRUE
chain_becomes_constant = Circuit()
chain_becomes_constant.add_inputs(['x'])
chain_becomes_constant.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
chain_becomes_constant.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
chain_becomes_constant.emplace_gate(
    'level1', gate.AND, ('x', 'false_const')
)  # -> FALSE
chain_becomes_constant.emplace_gate(
    'level2', gate.OR, ('level1', 'true_const')
)  # -> TRUE
chain_becomes_constant.set_outputs(['level2'])

expected_chain_becomes_constant = Circuit()
expected_chain_becomes_constant.add_inputs(['x'])
expected_chain_becomes_constant.emplace_gate('level2', gate.ALWAYS_TRUE, ())
expected_chain_becomes_constant.set_outputs(['level2'])


# =============================================================================
# Test cases for unused inputs preservation
# =============================================================================

# Test: Input becomes unused after simplification - should be preserved
# x is used, y becomes unused when AND(y, FALSE) -> FALSE
unused_input_preserved = Circuit()
unused_input_preserved.add_inputs(['x', 'y', 'z'])
unused_input_preserved.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
unused_input_preserved.emplace_gate(
    'g1', gate.AND, ('y', 'false_const')
)  # -> FALSE, y unused
unused_input_preserved.emplace_gate('g2', gate.OR, ('x', 'g1'))  # -> OR(x, FALSE) -> x
unused_input_preserved.set_outputs(['g2'])

expected_unused_input_preserved = Circuit()
expected_unused_input_preserved.add_inputs(['x', 'y', 'z'])
expected_unused_input_preserved.set_outputs(['x'])


# Test: All inputs become unused (output is just a constant)
all_inputs_unused = Circuit()
all_inputs_unused.add_inputs(['x', 'y'])
all_inputs_unused.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
all_inputs_unused.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
all_inputs_unused.emplace_gate('g1', gate.AND, ('x', 'false_const'))  # -> FALSE
all_inputs_unused.emplace_gate('g2', gate.OR, ('y', 'g1'))  # -> OR(y, FALSE) -> y
all_inputs_unused.emplace_gate('g3', gate.AND, ('g2', 'false_const'))  # -> FALSE
all_inputs_unused.set_outputs(['g3'])

expected_all_inputs_unused = Circuit()
expected_all_inputs_unused.add_inputs(['x', 'y'])
expected_all_inputs_unused.emplace_gate('g3', gate.ALWAYS_FALSE, ())
expected_all_inputs_unused.set_outputs(['g3'])


# =============================================================================
# Test cases for complex multi-path scenarios
# =============================================================================

# Test: Diamond with mixed simplification
#       TRUE
#      /    \
#   AND(x,T) OR(y,T)
#      \    /
#      XOR(l,r)  -> XOR(x, TRUE) -> NOT(x)
diamond_mixed = Circuit()
diamond_mixed.add_inputs(['x', 'y'])
diamond_mixed.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
diamond_mixed.emplace_gate('left', gate.AND, ('x', 'true_const'))  # -> x
diamond_mixed.emplace_gate('right', gate.OR, ('y', 'true_const'))  # -> TRUE
diamond_mixed.emplace_gate(
    'output', gate.XOR, ('left', 'right')
)  # -> XOR(x, TRUE) -> NOT(x)
diamond_mixed.set_outputs(['output'])

expected_diamond_mixed = Circuit()
expected_diamond_mixed.add_inputs(['x', 'y'])
expected_diamond_mixed.emplace_gate('output', gate.NOT, ('x',))
expected_diamond_mixed.set_outputs(['output'])


# Test: Multiple independent chains with different constants
multi_chain = Circuit()
multi_chain.add_inputs(['a', 'b', 'c'])
multi_chain.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
multi_chain.emplace_gate('false_const', gate.ALWAYS_FALSE, ())
multi_chain.emplace_gate('chain1', gate.AND, ('a', 'true_const'))  # -> a
multi_chain.emplace_gate('chain2', gate.OR, ('b', 'false_const'))  # -> b
multi_chain.emplace_gate('chain3', gate.XOR, ('c', 'true_const'))  # -> NOT(c)
multi_chain.emplace_gate('combine', gate.AND, ('chain1', 'chain2'))  # -> AND(a, b)
multi_chain.set_outputs(['combine', 'chain3'])

expected_multi_chain = Circuit()
expected_multi_chain.add_inputs(['a', 'b', 'c'])
expected_multi_chain.emplace_gate('chain3', gate.NOT, ('c',))
expected_multi_chain.emplace_gate('combine', gate.AND, ('a', 'b'))
expected_multi_chain.set_outputs(['combine', 'chain3'])


# Test: Reconvergent fanout - same signal used in multiple places
reconvergent = Circuit()
reconvergent.add_inputs(['x'])
reconvergent.emplace_gate('true_const', gate.ALWAYS_TRUE, ())
reconvergent.emplace_gate('g1', gate.AND, ('x', 'true_const'))  # -> x
reconvergent.emplace_gate('g2', gate.OR, ('x', 'true_const'))  # -> TRUE
reconvergent.emplace_gate('g3', gate.AND, ('g1', 'g2'))  # -> AND(x, TRUE) -> x
reconvergent.set_outputs(['g3'])

expected_reconvergent = Circuit()
expected_reconvergent.add_inputs(['x'])
expected_reconvergent.set_outputs(['x'])


# =============================================================================
# Parametrized tests
# =============================================================================


@pytest.mark.parametrize(
    "original_circuit, expected_circuit",
    [
        # Unary gates
        pytest.param(unary_not_true, expected_unary_not_true, id="NOT_ALWAYS_TRUE"),
        pytest.param(unary_not_false, expected_unary_not_false, id="NOT_ALWAYS_FALSE"),
        pytest.param(unary_iff_true, expected_unary_iff_true, id="IFF_ALWAYS_TRUE"),
        pytest.param(unary_iff_false, expected_unary_iff_false, id="IFF_ALWAYS_FALSE"),
        # AND gate
        pytest.param(
            and_with_true_right, expected_and_with_true_right, id="AND_x_TRUE"
        ),
        pytest.param(and_with_true_left, expected_and_with_true_left, id="AND_TRUE_x"),
        pytest.param(
            and_with_false_right, expected_and_with_false_right, id="AND_x_FALSE"
        ),
        pytest.param(
            and_with_false_left, expected_and_with_false_left, id="AND_FALSE_x"
        ),
        # OR gate
        pytest.param(or_with_true_right, expected_or_with_true_right, id="OR_x_TRUE"),
        pytest.param(
            or_with_false_right, expected_or_with_false_right, id="OR_x_FALSE"
        ),
        # XOR gate
        pytest.param(xor_with_true, expected_xor_with_true, id="XOR_x_TRUE"),
        pytest.param(xor_with_false, expected_xor_with_false, id="XOR_x_FALSE"),
        # NAND gate
        pytest.param(nand_with_true, expected_nand_with_true, id="NAND_x_TRUE"),
        pytest.param(nand_with_false, expected_nand_with_false, id="NAND_x_FALSE"),
        # NOR gate
        pytest.param(nor_with_true, expected_nor_with_true, id="NOR_x_TRUE"),
        pytest.param(nor_with_false, expected_nor_with_false, id="NOR_x_FALSE"),
        # NXOR gate
        pytest.param(nxor_with_true, expected_nxor_with_true, id="NXOR_x_TRUE"),
        pytest.param(nxor_with_false, expected_nxor_with_false, id="NXOR_x_FALSE"),
        # Comparison gates
        pytest.param(gt_with_false, expected_gt_with_false, id="GT_x_FALSE"),
        pytest.param(gt_with_true, expected_gt_with_true, id="GT_x_TRUE"),
        pytest.param(lt_with_true, expected_lt_with_true, id="LT_x_TRUE"),
        pytest.param(geq_with_false, expected_geq_with_false, id="GEQ_x_FALSE"),
        pytest.param(leq_with_true, expected_leq_with_true, id="LEQ_x_TRUE"),
        # Both operands constant
        pytest.param(and_both_true, expected_and_both_true, id="AND_TRUE_TRUE"),
        pytest.param(and_true_false, expected_and_true_false, id="AND_TRUE_FALSE"),
        pytest.param(or_both_false, expected_or_both_false, id="OR_FALSE_FALSE"),
        # Constant propagation
        pytest.param(
            propagation_chain, expected_propagation_chain, id="propagation_chain"
        ),
        pytest.param(
            complex_propagation, expected_complex_propagation, id="complex_propagation"
        ),
        # No constants
        pytest.param(no_constants, expected_no_constants, id="no_constants"),
        # Edge cases
        pytest.param(const_output, expected_const_output, id="const_output"),
        pytest.param(multi_output, expected_multi_output, id="multi_output"),
        pytest.param(
            duplicate_output, expected_duplicate_output, id="duplicate_output"
        ),
        # Deep chain propagation
        pytest.param(deep_chain, expected_deep_chain, id="deep_chain_4_levels"),
        pytest.param(
            chain_becomes_constant,
            expected_chain_becomes_constant,
            id="chain_becomes_constant",
        ),
        # Unused inputs preservation
        pytest.param(
            unused_input_preserved,
            expected_unused_input_preserved,
            id="unused_input_preserved",
        ),
        pytest.param(
            all_inputs_unused, expected_all_inputs_unused, id="all_inputs_unused"
        ),
        # Complex multi-path scenarios
        pytest.param(diamond_mixed, expected_diamond_mixed, id="diamond_mixed"),
        pytest.param(multi_chain, expected_multi_chain, id="multi_chain"),
        pytest.param(reconvergent, expected_reconvergent, id="reconvergent_fanout"),
    ],
)
def test_remove_constant_gates(original_circuit: Circuit, expected_circuit: Circuit):
    """Test that RemoveConstantGates correctly simplifies circuits with constants."""
    simplified = RemoveConstantGates().transform(original_circuit)
    assert simplified.inputs == expected_circuit.inputs
    assert simplified.outputs == expected_circuit.outputs
    assert simplified.get_truth_table() == expected_circuit.get_truth_table()


def test_remove_constant_gates_idempotent():
    """Test that RemoveConstantGates is idempotent - applying twice gives same result."""
    transformer = RemoveConstantGates()

    first_pass = transformer.transform(idempotency_test)
    second_pass = transformer.transform(first_pass)

    assert first_pass.inputs == second_pass.inputs
    assert first_pass.outputs == second_pass.outputs
    assert first_pass.get_truth_table() == second_pass.get_truth_table()


def test_remove_constant_gates_preserves_functionality():
    """Test that simplification preserves the circuit's boolean function."""
    circuits = [
        and_with_true_right,
        or_with_false_right,
        xor_with_true,
        propagation_chain,
        complex_propagation,
        no_constants,
        multi_output,
    ]

    for circuit in circuits:
        original_tt = circuit.get_truth_table()
        simplified = RemoveConstantGates().transform(circuit)
        simplified_tt = simplified.get_truth_table()
        assert original_tt == simplified_tt, f"Truth table mismatch for circuit"


def test_transformer_is_marked_idempotent():
    """Test that the transformer class correctly marks itself as idempotent."""
    transformer = RemoveConstantGates()
    assert transformer.is_idempotent is True
