from cirbo.core import TruthTable
from cirbo.synthesis.generation import generate_circuit_pm1971

parity = TruthTable([[False, True, True, False]])
circuit = generate_circuit_pm1971(parity)
circuit.view_graph(autorename_labels=True)
