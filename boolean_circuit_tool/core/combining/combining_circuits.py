from boolean_circuit_tool.core.circuit import Circuit, Gate, INPUT, NOT, AND, XOR, IFF, ALWAYS_FALSE, OR, Label


class CircuitBuilder:
    @staticmethod
    def generate_plus_one(inp_len : int, out_len : int) -> Circuit:
        x_labels = ['x_' + str(i) for i in range(inp_len)]
        z_labels = ['z_' + str(i) for i in range(out_len)]
        circuit = Circuit()
        for i in range(inp_len):
            circuit.add_gate(Gate(x_labels[i], INPUT))

        return circuit.add_plus_one(z_labels, x_labels)

    @staticmethod
    def generate_if_then_else() -> Circuit:
        return (Circuit().add_gate(Gate('if', INPUT, tuple()))
                            .add_gate(Gate('then', INPUT, tuple()))
                            .add_gate(Gate('else', INPUT, tuple()))
                            .add_if_then_else_of('if_then_else', 'if', 'then', 'else'))

    @staticmethod
    def generate_pairwise_if_then_else(n) -> Circuit:
        if_labels = ['if_'+str(i) for i in range(n)]
        then_labels = ['then_' + str(i) for i in range(n)]
        else_labels = ['else_' + str(i) for i in range(n)]
        if_then_else_labels = ['if_then_else_'+str(i) for i in range(n)]

        # circuit = (Circuit().add_block('if', CircuitBuilder.generate_inputs_with_labels(if_labels))
        #                     .add_block('then', CircuitBuilder.generate_inputs_with_labels(then_labels))
        #                     .add_block('else', CircuitBuilder.generate_inputs_with_labels(else_labels)))

        circuit = Circuit()
        for if_label in if_labels:
            circuit.add_gate(Gate(if_label, INPUT, tuple()))
        for then_label in then_labels:
            circuit.add_gate(Gate(then_label, INPUT, tuple()))
        for else_label in else_labels:
            circuit.add_gate(Gate(else_label, INPUT, tuple()))

        return circuit.add_pairwise_if_then_else_of(if_then_else_labels, if_labels, then_labels, else_labels)

    @staticmethod
    def generate_pairwise_xor(n : int) -> Circuit:
        x_labels = ['x_'+str(i) for i in range(n)]
        y_labels = ['y_'+str(i) for i in range(n)]
        xor_labels = ['xor_'+str(i) for i in range(n)]

        # circuit = (Circuit().add_block('x', CircuitBuilder.generate_inputs_with_labels(x_labels))
        #                     .add_block('y', CircuitBuilder.generate_inputs_with_labels(y_labels)))
        circuit = Circuit()
        for x_label in x_labels:
            circuit.add_gate(Gate(x_label, INPUT, tuple()))
        for y_label in y_labels:
            circuit.add_gate(Gate(y_label, INPUT, tuple()))

        return circuit.add_pairwise_xor(xor_labels, x_labels, y_labels)

    @staticmethod
    def generate_inputs_with_labels(labels: list[Label]) -> Circuit:
        circuit = Circuit()
        for label in labels:
            circuit.add_gate(Gate(label, INPUT, tuple()))
        return circuit

    @staticmethod
    def generate_inputs(n: int) -> Circuit:
        return CircuitBuilder.generate_inputs_with_labels(['x'+str(i) for i in range(n)])


class CircuitCombiner:
    @staticmethod
    def miter_of(circuit1 : Circuit, circuit2 : Circuit) -> Circuit:
        assert(circuit1.input_size == circuit2.input_size)
        assert(circuit1.output_size == circuit2.output_size)

        n = circuit1.input_size
        m = circuit1.output_size

        circuit = (Circuit().add_block('circuit1', circuit1)
                            .add_block('circuit2', circuit2)
                            .add_block('pairwise_xor', CircuitBuilder.generate_pairwise_xor(m))
                            .add_block('inputs', CircuitBuilder.generate_inputs(n)))

        circuit.connect(circuit.get_block('circuit1'), circuit.get_block('pairwise_xor').get_block('x'))
        circuit.connect(circuit.get_block('circuit2'), circuit.get_block('pairwise_xor').get_block('y'))

        circuit.add_gate(Gate('big_or', OR, tuple(circuit.get_block('pairwise_xor').get_outputs())))

        circuit.connect(circuit.get_block('inputs'), circuit.get_block('circuit1'))
        circuit.connect(circuit.get_block('inputs'), circuit.get_block('circuit2'))

        circuit.mark_as_output('big_or')

        return circuit
