from boolean_circuit_tool.core.circuit import Circuit, Gate


__all__ = ['are_circuits_isomorphic']


def are_circuits_isomorphic(circuit1: Circuit, circuit2: Circuit) -> bool:
    def topological_sort_compare(circuit: Circuit, inverse: bool = False) -> list[Gate]:
        return list(circuit.top_sort(inverse=inverse))

    sorted_gates1 = topological_sort_compare(circuit1)
    sorted_gates2 = topological_sort_compare(circuit2)

    if len(sorted_gates1) != len(sorted_gates2):
        return False

    for gate1, gate2 in zip(sorted_gates1, sorted_gates2):
        if gate1.gate_type != gate2.gate_type:
            return False

        if len(gate1.operands) != len(gate2.operands):
            return False

    return True
