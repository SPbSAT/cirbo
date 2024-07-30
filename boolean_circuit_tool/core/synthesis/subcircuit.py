import collections
import copy
import itertools
import json

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate
from boolean_circuit_tool.core.truth_table import TruthTableModel
from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat, Basis, get_tt_by_str
from boolean_circuit_tool.synthesis.exception import NoSolutionError


class Subcircuit():
    def __init__(self, inputs = None, gates = None, outputs = None, size = 0, inputs_tt = None, patterns = None):
        self.inputs = [] if inputs is None else inputs
        self.gates = [] if gates is None else gates # gates are in topsort order
        self.outputs = [] if outputs is None else outputs
        self.size = size
        self.inputs_tt = [] if inputs_tt is None else inputs_tt
        self.patterns = collections.defaultdict(int) if patterns is None else patterns

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

        for i in itertools.product(('0', '1'), repeat=n):
            assignment = ''.join(i)
            assignment = assignment[::-1] # todo: check if needed
            for j, pattern in enumerate(output_patterns):
                bit = str(pattern & 1)
                output_patterns[j] >>= 1
                truth_table[j] += bit if assignment in inputs_tt else '*'
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
        patterns_raw = subcircuit_json.get('patterns', collections.defaultdict(int))
        patterns = collections.defaultdict(int)
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
    cut_nodes = collections.defaultdict(set)
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
    return itertools.chain.from_iterable(itertools.combinations(lst, x) for x in range(len(lst) + 1))


def generate_inputs_tt(sizes: list[int]):
    inputs_tt = collections.defaultdict(list)
    for size in sizes:
        inputs_tt[size] = [0] * size
        for i in range(1 << size):
            for j in range(size):
                inputs_tt[size][j] += ((i >> j) & 1) << i
    return inputs_tt


def top_sort(circuit):
    vis = collections.defaultdict(bool)
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

def is_cyclic(circuit):
    sorted_gates = top_sort(circuit)
    gate_position = {gate: i for i, gate in enumerate(sorted_gates)}
    for gate in sorted_gates:
        for operand in circuit.get_element(gate).operands:
            if gate_position[gate] < gate_position[operand]:
                return True
    return False

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
    is_removed = collections.defaultdict(bool)
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
        inputs_lst = list(inputs)
        outputs = []
        nodes = sorted(list(cut_nodes[cut]), key=lambda x: node_pos[x])

        circuit_tt = collections.defaultdict(int)
        circuit_size = 0
        MAX_PATTERN = (1 << (1 << n)) - 1
        for i, node in enumerate(inputs_lst):
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
            is_output = node in outputs_set
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
                inputs=list(inputs_lst)[::-1],
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
    truth_table = collections.defaultdict(list)

    for i in range(1 << len(inputs)):
        if i: # update assignment for new iteration
            idx = len(inputs) - 1
            while assignment[inputs[idx]]:
                assignment[inputs[idx]] = False
                idx -= 1
            assignment[inputs[idx]] = True
        for gate, value in circuit.evaluate_circuit(assignment).items():
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
    # circuit = Circuit.from_bench('./core/synthesis/ex20.bench')
    # cuts_path = './core/synthesis/cuts20.txt'

    # circuit = Circuit.from_bench('./core/synthesis/my_ex.bench')
    # cuts_path = './core/synthesis/my_cuts.txt'

    circuit = Circuit.from_bench('./core/synthesis/test/sum5_size12.bench')
    cuts_path = './core/synthesis/test/sum5_cuts.txt'

    initial_circuit = copy.deepcopy(circuit)
    basis = Basis.XAIG

    inputs_tt = generate_inputs_tt([3, 4, 5])
    subcircuits = process_cuts(circuit, cuts_path)
    subcircuits = eval_dont_cares(circuit, subcircuits)

    gate_status = collections.defaultdict(str)

    for iter, subcircuit in enumerate(subcircuits):
        inputs = subcircuit.inputs
        inputs_set = set(inputs)
        outputs_set = set(subcircuit.outputs)
        size = subcircuit.size

        if size > 11:
            continue

        skip_subcircuit = False
        for gate in subcircuit.gates:
            if gate_status[gate] == 'removed':
                skip_subcircuit = True
                break
            if gate_status[gate] == 'modified' and gate not in inputs_set:
                skip_subcircuit = True
                break

        if skip_subcircuit:
            continue

        found_patterns = collections.defaultdict(int)
        for input in inputs:
            found_patterns[subcircuit.patterns[input]] = input

        MAX_PATTERN = (1 << (1 << len(inputs))) - 1
        filtered_outputs = set()
        filtered_outputs_lst = []
        outputs_mapping = collections.defaultdict(int)
        outputs_negation_mapping = collections.defaultdict(int)

        for output in subcircuit.outputs:
            pattern = subcircuit.patterns[output]
            if pattern in found_patterns:
                outputs_mapping[output] = found_patterns[pattern]
            elif MAX_PATTERN - pattern in found_patterns:
                outputs_negation_mapping[output] = found_patterns[pattern]
            else:
                filtered_outputs.add(output)
                filtered_outputs_lst.append(output)
                found_patterns[pattern] = output

        outputs_tt = []
        for i, row in enumerate(subcircuit.evaluate_truth_table_with_dont_cares()):
            if subcircuit.outputs[i] in filtered_outputs:
                outputs_tt.append(row)

        new_subcircuit = None
        try:
            new_subcircuit = CircuitFinderSat(
                TruthTableModel(get_tt_by_str(outputs_tt)), size - 1, basis=basis
            ).find_circuit()
        except NoSolutionError:
            pass

        if new_subcircuit is None:
            continue

        print(outputs_tt)
        print(f'Inputs: {inputs}')
        print(f'Outputs: {subcircuit.outputs}')

        new_subcircuit.save_to_file('check_subcircuit.bench')

        old_gates_to_new_mapping = {}
        new_gates_to_old_mapping = {}

        # print(inputs)
        # print(filtered_outputs)
        # print('checking this ==========')

        for i, old_gate in enumerate(inputs):
            new_gate = new_subcircuit.inputs[i]
            old_gates_to_new_mapping[old_gate] = new_gate
            new_gates_to_old_mapping[new_gate] = old_gate

        for i, old_gate in enumerate(filtered_outputs_lst):
            new_gate = new_subcircuit.outputs[i]
            old_gates_to_new_mapping[old_gate] = new_gate
            new_gates_to_old_mapping[new_gate] = old_gate

        # Changing initial circuit
        new_circuit = copy.deepcopy(circuit)
        new_gate_counter = 0

        # Add new gates
        new_inputs = set(new_subcircuit.inputs)
        new_outputs = set(new_subcircuit.outputs)

        # new_gate_mapping = {}
        # for i, new_gate in enumerate(new_subcircuit.inputs):
            # new_gate_mapping[new_gate] = inputs[i]

        for new_gate in top_sort(new_subcircuit):
            if new_gate in new_inputs:
                continue
            elif new_gate in new_outputs:
                old_gate = new_gates_to_old_mapping[new_gate]

                gate_type = new_subcircuit.get_element(new_gate).gate_type
                operands = new_subcircuit.get_element(new_gate).operands
                new_circuit.get_element(old_gate)._gate_type = gate_type
                new_circuit.get_element(old_gate)._operands = tuple([new_gates_to_old_mapping[x] for x in operands])
                for x in operands:
                    new_circuit._add_user(new_gates_to_old_mapping[x], gate)
            else:
                gate_type = new_subcircuit.get_element(new_gate).gate_type
                operands = new_subcircuit.get_element(new_gate).operands
                new_gates_to_old_mapping[new_gate] = f'x{iter}_{new_gate_counter}'
                new_gate_counter += 1

                gate_to_add = Gate(
                    label=new_gates_to_old_mapping[new_gate],
                    gate_type=gate_type,
                    operands=tuple([new_gates_to_old_mapping[x] for x in operands])
                )
                new_circuit.add_gate(gate_to_add)

        for output, mapped_gate in outputs_mapping.items():
            if output != mapped_gate:
                print('BAD CASE 1')

        for output, mapped_gate in outputs_negation_mapping.items():
            gate_type = new_subcircuit.get_element(output).gate_type
            operands = new_subcircuit.get_element(output).operands

            if gate_type.name != 'NOT' or operands[0] != mapped_gate:
                print('BAD CASE 2')

        # Remove old gates
        for gate in subcircuit.gates:
            if gate in inputs_set or gate in outputs_set:
                continue
            # print(gate, new_circuit.has_element(gate))
            # print(new_circuit.get_element(gate))
            new_circuit.remove_gate(new_circuit.get_element(gate))
        
        if is_cyclic(new_circuit):
            continue

        circuit = new_circuit
        print('Improved circuit by 1 gate')

        # print(inputs_set, 'check')
        for output in filtered_outputs:
            gate_status[output] = 'modified'
    
        for gate in subcircuit.gates:
            if gate in inputs_set or gate in outputs_set:
                continue
            gate_status[gate] = 'removed'

        circuit.save_to_file(f'circuit_v{iter}.txt')

    # Sanity check
    assignment = {input: False for input in initial_circuit.inputs}
    circuit.save_to_file('new_circuit.bench')
    for i in range(1 << len(initial_circuit.inputs)):
        if i: # update assignment for new iteration
            idx = len(inputs) - 1
            while assignment[inputs[idx]]:
                assignment[inputs[idx]] = False
                idx -= 1
            assignment[inputs[idx]] = True
        assert circuit.evaluate_circuit_outputs(assignment) == initial_circuit.evaluate_circuit_outputs(assignment), "Initial circuit and circuit after impovement differ"

    print('Check passed')
    # circuit.save_to_file('new_circuit.bench')
