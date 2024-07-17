from collections import defaultdict
from itertools import chain, combinations
import json
import re

from typing import List

from boolean_circuit_tool.core.circuit import Circuit


class Subcircuit():
    def __init__(self, inputs = [], gates = [], outputs = [], size = 0, inputs_tt = [], patterns = defaultdict(int)):
        self.inputs = inputs
        self.gates = gates
        self.outputs = outputs
        self.size = size
        self.inputs_tt = inputs_tt
        self.patterns = patterns

    @property
    def key(self):
        return tuple([len(self.inputs)] + sorted([self.patterns[output] for output in self.outputs]))
    
    def evaluate_truth_table_with_dont_cares(self):
        """
        Returns truth table with don't cares based on possible inputs assignments (stored in `inputs_tt` field)
        """
        inputs_tt = self.inputs_tt
        output_patterns = [self.patterns[gate] for gate in self.outputs]
        truth_table = ['' for i in range(len(output_patterns))]
        n = len(self.inputs)

        for i in range(1 << n):
            tmp = i
            assignment = ''
            for j in range(n):
                assignment += str(tmp % 2)
                tmp //= 2
            assignment = assignment[::-1] # todo: check if needed
            for j, pattern in enumerate(output_patterns):
                bit = str(pattern % 2)
                output_patterns[j] //= 2
                if assignment in inputs_tt:
                    truth_table[j] += bit
                else:
                    truth_table[j] += '*'
        return truth_table

    def serialize(self):
        return {
            'inputs': self.inputs,
            'gates': self.gates,
            'outputs': self.outputs,
            'size': self.size,
            'inputs_tt': self.inputs_tt,
            'patterns': self.patterns
        }

    @staticmethod
    def deserialize(subcircuit_json):
        inputs = subcircuit_json.get('inputs', [])
        gates = subcircuit_json.get('gates', [])
        outputs = subcircuit_json.get('outputs', [])
        size = subcircuit_json.get('size', 0)
        inputs_tt = subcircuit_json.get('inputs_tt', [])
        patterns_raw = subcircuit_json.get('patterns', defaultdict(int))
        patterns = defaultdict(int)
        for key, val in patterns_raw.items():
            patterns[key] = val

        return Subcircuit(
            inputs=inputs,
            gates=gates,
            outputs=outputs,
            size=size,
            inputs_tt=inputs_tt,
            patterns=patterns
        )
        
    def deserialize_array_from_file(filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        subcircuits = []
        for subcircuit_raw in data:
            subcircuits.append(Subcircuit.deserialize(subcircuit_raw))
        return subcircuits
    
    @staticmethod
    def dump_list_to_file(subcircuits, filename):
        subcircuits_raw = [subcircuit.serialize() for subcircuit in subcircuits]
        with open(filename, 'w') as f:
            json.dump(subcircuits_raw, f, indent=4)


def read_cuts(filename):
    cut_nodes = defaultdict(set)
    with open(filename, 'r') as f:
        for line in f.readlines():
            if line == '\n':
                continue
            data = line.split()
            if data[0] == 'Node:':
                node = data[1]
            else:
                cut = tuple(x for x in data[1:-1])
                cut_nodes[cut].add(node)
    return cut_nodes


def powerset(iterable):
    lst = list(iterable)
    return chain.from_iterable(combinations(lst, x) for x in range(len(lst) + 1))


def generate_inputs_tt(sizes: List[int]):
    inputs_tt = defaultdict(list)
    for size in sizes:
        inputs_tt[size] = [0 for i in range(size)]
        for i in range(1 << size):
            for j in range(size):
                inputs_tt[size][j] += ((i & (1 << j)) >> j) << i
    return inputs_tt


def top_sort(circuit):
    vis = defaultdict(bool)
    sorted_gates = []
    def dfs(gate):
        vis[gate] = True
        for next_gate in circuit.get_element(gate).operands:
            if not vis[next_gate]:
                dfs(next_gate)
        sorted_gates.append(gate)

    for output in circuit.outputs:
        if not vis[output]:
            dfs(output)
    return sorted_gates


def process_cuts(circuit, cuts_path):
    cut_nodes = read_cuts(cuts_path)
    cuts = sorted(cut_nodes.keys(), key=lambda x: len(x))

    print(f'Found {len(cuts)} cuts')

    def is_nested_cut(cut1, cut2) -> bool:
        """
        Returns: `True` if `cut1` is nested in `cut2, otherwise: `False`
        """
        for gate in cut1:
            in_cut = False
            for subcut in powerset(cut2):
                if gate in cut_nodes[subcut]:
                    in_cut = True
                    break
            if not in_cut:
                return False
        return True

    good_cuts = []
    is_removed = defaultdict(bool)
    for i, cut in enumerate(cuts):
        for subcut in powerset(cut): # check whether cut should be removed
            if is_removed[subcut]:
                is_removed[cut] = True
                break
        if is_removed[cut]:
            continue
        for prev_cut in good_cuts:
            if is_nested_cut(cut, prev_cut):
                is_removed[cut] = True
                break
        if is_removed[cut]:
            continue

        for next_cut in cuts[i+1:]:
            if len(next_cut) > len(cut):
                break
            if is_nested_cut(cut, next_cut):
                is_removed[cut] = True
                break
        if is_removed[cut]:
            continue
        good_cuts.append(cut)

    print(f'Removed {len(cuts) - len(good_cuts)} nested cuts')

    # Fill cuts with all its gates
    for cut in good_cuts:
        for subcut in powerset(cut):
            cut_nodes[cut].update(cut_nodes[subcut])

    sorted_gates = top_sort(circuit)
    node_pos = {node: i for i, node in enumerate(sorted_gates)}
    subcircuits = []
    good_cuts = [cut for cut in good_cuts if len(cut) > 2] # skip small cuts

    print(f'Process: {len(good_cuts)} cuts')

    outputs_set = set(circuit.outputs)

    for cut in good_cuts:
        n = len(cut)
        inputs = set(cut)
        outputs = []
        nodes = sorted(list(cut_nodes[cut]), key=lambda x: node_pos[x])

        circuit_tt = defaultdict(int)
        circuit_size = 0
        MAX_PATTERN = (1 << (1 << n)) - 1
        for i, node in enumerate(inputs):
            circuit_tt[node] = inputs_tt[n][i]
        for node in nodes:
            if node in inputs:
                continue

            operands = circuit.get_element(node).operands
            users = circuit.get_element_users(node)
            oper_type = circuit.get_element(node).gate_type.name

            if len(operands) == 1:
                assert operands[0] in circuit_tt, f'{cut} {node} {operands} {oper_type}' 
                circuit_tt[node] = MAX_PATTERN - circuit_tt[operands[0]]
            else:
                assert operands[0] in circuit_tt and operands[1] in circuit_tt, f'{cut} {node} {operands} {oper_type}' 
                if oper_type == 'AND':
                    circuit_tt[node] = circuit_tt[operands[0]] & circuit_tt[operands[1]]
                elif oper_type == 'NAND':
                    circuit_tt[node] = MAX_PATTERN - (circuit_tt[operands[0]] & circuit_tt[operands[1]])
                elif oper_type == 'OR':
                    circuit_tt[node] = circuit_tt[operands[0]] | circuit_tt[operands[1]]
                elif oper_type == 'NOR':
                    circuit_tt[node] = MAX_PATTERN - (circuit_tt[operands[0]] | circuit_tt[operands[1]])
                elif oper_type == 'XOR':
                    circuit_tt[node] = circuit_tt[operands[0]] ^ circuit_tt[operands[1]]
                elif oper_type == 'NXOR':
                    circuit_tt[node] = MAX_PATTERN - (circuit_tt[operands[0]] ^ circuit_tt[operands[1]])
                else:
                    print('Error! Incorrect operation')
                    assert False
                circuit_size += 1
            is_output = circuit in outputs_set
            if not is_output:
                for user in users:
                    if user not in cut_nodes[cut]:
                        is_output = True
                        break
            if is_output:
                outputs.append(node)
        outputs.sort(key=lambda x: circuit_tt[x])
        outputs_tt = {circuit_tt[output] for output in outputs}
        subcircuits.append(
            Subcircuit(
                inputs=list(inputs)[::-1],
                gates=nodes,
                outputs=outputs,
                size=circuit_size,
                patterns=circuit_tt
            )
        )
    return subcircuits


def eval_dont_cares(circuit, subcircuits):
    inputs = circuit.inputs
    assignment = {input: False for input in inputs}
    truth_table = defaultdict(list)

    for i in range(1 << len(inputs)):
        if i: # update assignment for new iteration
            idx = len(inputs) - 1
            while assignment[inputs[idx]]:
                assignment[inputs[idx]] = False
                idx -= 1
            assignment[inputs[idx]] = True
        for gate, value in circuit.evaluate_full_circuit(assignment).items():
            truth_table[gate].append(int(value))

    for subcircuit in subcircuits:
        possible_assignments = set()
        for i in range(1 << len(inputs)):
            curr_assignment = []
            for input in subcircuit.inputs:
                curr_assignment.append(str(truth_table[input][i]))
            possible_assignments.add(''.join(curr_assignment))
        subcircuit.inputs_tt = sorted(possible_assignments)
    return subcircuits


if __name__ == '__main__':
    circuit = Circuit.from_bench(open('./core/synthesis/ex20.bench'))
    cuts_path = './core/synthesis/cuts20.txt'

    inputs_tt = generate_inputs_tt([3, 4, 5])
    subcircuits = process_cuts(circuit, cuts_path)
    subcircuits = eval_dont_cares(circuit, subcircuits)
    # Subcircuit.dump_list_to_file(subcircuits, 'subcircuits.txt')
