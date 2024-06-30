#
# This file presents an example of a potential way to build a circuit from blocks.
#

from сircuit import Circuit, Block


# Given a Circuit with 2*n inputs, return n.
def get_n(circuit: Circuit) -> int:
    return len(circuit.get_inputs()) // 2


# Given a circuit with inputs x_n, ..., x_1, y_n, ..., y_1, and outputs z_2n, ..., z_1,
# we build c0 in the following way:
#
#   1) assign 0...0 to x_n...x_1;
#   2) add big OR to z_2n...z_1, let its output gate be z.
#
# The final circuit has y_n...y_1 as inputs and z as output.
#
# Below are two versions of how we potentially want to construct c0.
def build_c0_version1(circuit: Circuit) -> Circuit:
    n = get_n(circuit)

    c0 = Circuit()
    block_or = c0.add_block('or', Circuit.generate_OR(2*n))
    block_c = c0.add_block('c', circuit)

    c0.connect(block_c, block_or)
    c0.assign([0]*n, block_c.get_inputs()[:n])

    c0.set_outputs(block_or.get_outputs())

    return c0


def build_c0_version2(circuit: Circuit) -> Circuit:
    n = get_n(circuit)

    return Circuit.generate_OR(2*n).substitute_inputs(
                circuit.substitute_inputs([0]*n, circuit.get_inputs()[:n]))


# Given a circuit with inputs x = x_n...x_1, y = y_n...y_1, and outputs z_h = z_2n...z_(n+1), z_l = z_n...z_1,
# we build c1 in the following way:
#
#   1) substitute x with x+1 (n bits);
#   2) if x == 1...1 then replace z_h with y.
#
def build_c1(circuit: Circuit) -> Circuit:
    n = get_n(circuit)

    c1 = Circuit()
    block_c : Block = c1.add_block('c', circuit)
    block_x_plus_one : Block = c1.add_block('x_plus_one', Circuit.generate_PLUS_ONE(inp_len=n, out_len=n + 1))
    block_if_then_else : Block = c1.add_block('if_then_else', Circuit.generate_PAIRWISE_IF_THEN_ELSE(n))

    c1.connect(block_x_plus_one.get_outputs()[1:], block_c.get_block('x'))
    c1.connect(block_x_plus_one.get_outputs()[:1]*n, block_if_then_else.get_block('if'))
    c1.connect(block_c.get_block('y'), block_if_then_else.get_block('then'))
    c1.connect(block_c.get_block('z_h'), block_if_then_else.get_block('else'))

    c1.set_outputs(block_if_then_else.get_outputs() + block_c.get_block('z_l').get_outputs())

    return c1


# Given a circuit with inputs x = x_n...x_1, y = y_n...y_1, and outputs z = z_2n...z_1,
# we build c1 in the following way:
#
#   1) add y to z.
#
def build_c2(circuit: Circuit) -> Circuit:
    n = get_n(circuit)

    c2 = Circuit()
    block_c : Block = c2.add_block('c', circuit)
    block_plus_y : Block = c2.add_block('plus_y', Circuit.generate_summator(x_len=2*n, y_len=n, z_len=2*n))

    c2.connect(block_c, block_plus_y.get_block('x'))
    c2.connect(c2.get_block('y'), block_plus_y.get_block('y'))

    c2.set_outputs(block_plus_y.get_outputs())

    return c2


# For a given circuit with 2*n inputs and 2*n outputs, mark its inputs as 'x' and 'y', and outputs as 'z_h' and 'z_l'.
def make_multiplier_blocks(circuit: Circuit):
    n = get_n(circuit)

    circuit.make_block('x', circuit.get_inputs()[:n])
    circuit.make_block('y', circuit.get_inputs()[n:])
    circuit.make_block('z_h', circuit.get_outputs()[:n])
    circuit.make_block('z_l', circuit.get_outputs()[n:])


# Given a circuit, build a new circuit that is satisfiable if and only if the given circuit is a multiplier.
def build_verifier(circuit: Circuit) -> Circuit:
    make_multiplier_blocks(circuit)

    c0 = build_c0_version1(circuit.copy())
    c1 = build_c1(circuit.copy())
    c2 = build_c2(circuit.copy())

    return Circuit.OR(c0, Circuit.miter(c1, c2))
