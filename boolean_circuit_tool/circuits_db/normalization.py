import typing as tp

from boolean_circuit_tool.core.boolean_function import RawTruthTable
from boolean_circuit_tool.core.circuit import Circuit


class NormalizationInfo:
    def __init__(self):
        self.negations: tp.Optional[tp.List[bool]] = None
        self.permutation: tp.Optional[tp.List[int]] = None
        self.mapping: tp.Optional[tp.List[int]] = None

    def normalize(self, truth_table: RawTruthTable) -> RawTruthTable:
        assert self.negations is None
        assert self.permutation is None
        assert self.mapping is None

        truth_table = self._normalize_outputs(truth_table)
        truth_table = self._sort_outputs(truth_table)
        truth_table = self._delete_duplicate_outputs(truth_table)
        return truth_table

    def denormalize(self, circuit: Circuit) -> Circuit:
        assert self.negations is not None
        assert self.permutation is not None
        assert self.mapping is not None

        ...
        # TODO
        return circuit

    def _normalize_outputs(self, truth_table: RawTruthTable) -> RawTruthTable:
        new_truth_table: RawTruthTable = []
        negations: tp.List[bool] = []
        for tt in truth_table:
            if tt[0]:
                negations.append(True)
                new_truth_table.append([not value for value in tt])
            else:
                negations.append(False)
                new_truth_table.append(tt)
        self.negations = negations
        return new_truth_table

    def _denormalize_outputs(self, circuit: Circuit) -> Circuit:
        ...

    def _sort_outputs(self, truth_table: RawTruthTable) -> RawTruthTable:
        enumerated_truth_tables = list(enumerate(truth_table))
        enumerated_truth_tables.sort(key=lambda x: x[1])
        new_truth_table = [x[1] for x in enumerated_truth_tables]
        self.permutation = [x[0] for x in enumerated_truth_tables]
        return new_truth_table

    def _delete_duplicate_outputs(self, truth_table: RawTruthTable) -> RawTruthTable:
        # assumes outputs are sorted
        new_truth_table = [truth_table[0]]
        mapping = [0]
        for i in range(1, len(truth_table)):
            if truth_table[i] != truth_table[i - 1]:
                new_truth_table.append(truth_table[i])
            mapping.append(len(new_truth_table) - 1)
        self.mapping = mapping
        return new_truth_table
