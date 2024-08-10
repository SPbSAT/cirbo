from boolean_circuit_tool.core.circuit import Circuit, Gate, INPUT, OR, Label, AND, NOT, XOR, IFF, ALWAYS_FALSE


def generate_plus_one(inp_len: int, out_len: int) -> Circuit:
    x_labels = ['x_' + str(i) for i in range(inp_len)]
    z_labels = ['z_' + str(i) for i in range(out_len)]
    circuit = Circuit()
    for i in range(inp_len):
        circuit.add_gate(Gate(x_labels[i], INPUT))

    return add_plus_one(circuit, z_labels, x_labels)


def generate_if_then_else() -> Circuit:
    circuit = (Circuit().add_gate(Gate('if', INPUT))
            .add_gate(Gate('then', INPUT))
            .add_gate(Gate('else', INPUT)))

    return add_if_then_else_of(circuit, 'if_then_else', 'if', 'then', 'else')


def generate_pairwise_if_then_else(n) -> Circuit:
    if_labels = ['if_' + str(i) for i in range(n)]
    then_labels = ['then_' + str(i) for i in range(n)]
    else_labels = ['else_' + str(i) for i in range(n)]
    if_then_else_labels = ['if_then_else_' + str(i) for i in range(n)]

    circuit = Circuit()
    circuit.add_inputs(if_labels)
    circuit.add_inputs(then_labels)
    circuit.add_inputs(else_labels)

    return add_pairwise_if_then_else_of(circuit, if_then_else_labels, if_labels, then_labels, else_labels)


def generate_pairwise_xor(n: int) -> Circuit:
    x_labels = ['x_' + str(i) for i in range(n)]
    y_labels = ['y_' + str(i) for i in range(n)]
    xor_labels = ['xor_' + str(i) for i in range(n)]

    circuit = Circuit()
    circuit.add_inputs(x_labels)
    circuit.add_inputs(y_labels)

    return add_pairwise_xor(circuit, xor_labels, x_labels, y_labels)


def generate_inputs_with_labels(labels: list[Label]) -> Circuit:
    circuit = Circuit()
    for label in labels:
        circuit.add_gate(Gate(label, INPUT, tuple()))
        circuit.mark_as_output(label)
    return circuit


def generate_inputs(n: int) -> Circuit:
    return generate_inputs_with_labels(['x' + str(i) for i in range(n)])


def add_plus_one(circuit : Circuit, result_labels, x_labels) -> Circuit:
    inp_len = len(x_labels)
    out_len = len(result_labels)

    circuit.add_gate(Gate('carry_0', IFF, tuple([x_labels[0]])))
    circuit.add_gate(Gate(result_labels[0], NOT, tuple([x_labels[0]]))).mark_as_output(result_labels[0])

    for i in range(1, out_len):
        if i < inp_len:
            if i < out_len - 1:
                circuit.add_gate(Gate('carry_' + str(i), AND, ('x_' + str(i), 'carry_' + str(i - 1))))
            circuit.add_gate(Gate('z_' + str(i), XOR, ('x_' + str(i), 'carry_' + str(i - 1))))
        elif i == inp_len:
            circuit.add_gate(Gate('z_' + str(i), IFF, tuple(['carry_' + str(i - 1)])))
        else:
            circuit.add_gate(Gate('z_' + str(i), ALWAYS_FALSE, tuple()))
        circuit.mark_as_output('z_' + str(i))

    return circuit.order_outputs(['z_' + str(i) for i in range(out_len)])


def add_if_then_else_of(circuit, result_label: Label, if_label: Label, then_label: Label,
                        else_label: Label) -> Circuit:
    (circuit.add_gate(Gate('tmp1' + result_label, AND, (if_label, then_label)))
     .add_gate(Gate('tmp2' + result_label, NOT, tuple([if_label])))
     .add_gate(Gate('tmp3' + result_label, AND, ('tmp2' + result_label, else_label)))
     .add_gate(Gate(result_label, OR, ('tmp1' + result_label, 'tmp3' + result_label)))
     .mark_as_output(result_label))
    return circuit


def add_pairwise_if_then_else_of(circuit, result_labels, if_inputs, then_inputs, else_inputs) -> Circuit:
    assert (len(if_inputs) == len(then_inputs) == len(else_inputs))
    n = len(if_inputs)
    for i in range(n):
        add_if_then_else_of(circuit, result_labels[i], if_inputs[i], then_inputs[i], else_inputs[i])

    return circuit


def add_pairwise_xor(circuit, result_labels, x_labels, y_labels) -> Circuit:
    assert (len(x_labels) == len(y_labels))
    n = len(x_labels)
    for i in range(n):
        circuit.add_gate(Gate(result_labels[i], XOR, (x_labels[i], y_labels[i])))
        circuit.mark_as_output(result_labels[i])
    return circuit
