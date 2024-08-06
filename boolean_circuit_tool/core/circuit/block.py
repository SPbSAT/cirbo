import typing as tp

from boolean_circuit_tool.core.circuit.gate import Label

__all__ = ['Block']

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Circuit

class Block():
    def __init__(
        self, 
        name: Label, 
        circuit: 'Circuit', 
        inputs: list[Label], 
        gates: list[Label], 
        outputs: list[Label],
    ):
        self._name = name
        self._circuit_ref = circuit
        self._inputs = inputs
        self._gates = gates
        self._outputs = outputs

    @property
    def name(self) -> Label:
        return self._name
    
    @property
    def inputs(self) -> list[Label]:
        return self._inputs
    
    @property
    def gates(self) -> list[Label]:
        return self._gates
    
    @property
    def outputs(self) -> list[Label]:
        return self._outputs
    
    @property
    def circuit_ref(self) -> 'Circuit':
        return self._circuit_ref

    def into_circuit():
        pass