"""Preparata--Muller synthesis for fully defined Boolean functions."""

import dataclasses
import enum
import itertools
import typing as tp

from cirbo.core.boolean_function import Function, RawTruthTable
from cirbo.core.circuit import Circuit, gate
from cirbo.core.circuit.gate import GateType, Label

__all__ = [
    "generate_circuit_pm1971",
]

_COMPLETE_SEARCH_DEPTH = 3
_THREE_VARIABLE_TAIL_SIZE = 3
_FOUR_VARIABLE_TAIL_SIZE = 4
# Normal-form cofactors are limited to 2**8 rows. One recursive split then supports
# a cofactor as large as the whole direct construction can handle: 2**8 + 8 inputs.
_MAX_DIRECT_TAIL_SIZE = 8
_MAX_RECURSIVE_TAIL_SIZE = (1 << _MAX_DIRECT_TAIL_SIZE) + _MAX_DIRECT_TAIL_SIZE

_TruthTableMask = int


class _BinaryOperation(enum.Enum):
    AND = enum.auto()
    OR = enum.auto()


@dataclasses.dataclass(frozen=True)
class _ConstantExpression:
    value: bool


@dataclasses.dataclass(frozen=True)
class _LiteralExpression:
    variable: int
    negated: bool


@dataclasses.dataclass(frozen=True)
class _BinaryExpression:
    operation: _BinaryOperation
    left: "_Expression"
    right: "_Expression"


_Expression = tp.Union[
    _ConstantExpression,
    _LiteralExpression,
    _BinaryExpression,
]


@dataclasses.dataclass(frozen=True)
class _ExpressionWithDepth:
    depth: int
    expression: _Expression


class _PreparataMullerBuilder:
    def __init__(self, input_size: int, truth_table: RawTruthTable):
        self.circuit = Circuit.bare_circuit(input_size)
        self.inputs = self.circuit.inputs
        self._next_gate = 0
        self._constants: tp.Dict[bool, Label] = {}

        # These per-build caches are released with the builder. A module-level cache
        # would retain exponentially-sized expression databases for the process lifetime.
        self._expression_databases: tp.Dict[
            tp.Tuple[int, int],
            tp.Dict[_TruthTableMask, _ExpressionWithDepth],
        ] = {}
        self._expression_searches: tp.Dict[
            tp.Tuple[_TruthTableMask, int, int],
            tp.Optional[_Expression],
        ] = {}

        self.negated_inputs = [
            self._add_gate(gate.NOT, (input_label,)) for input_label in self.inputs
        ]

        variables = list(reversed(range(len(self.inputs))))
        for output in truth_table:
            output_gate = self._build_recursive(output, variables, True)
            self.circuit.mark_as_output(output_gate)

    def _small_expression_database(
        self,
        variable_count: int,
        maximum_depth: int,
    ) -> tp.Dict[_TruthTableMask, _ExpressionWithDepth]:
        cache_key = (variable_count, maximum_depth)
        cached = self._expression_databases.get(cache_key)
        if cached is not None:
            return cached

        value_count = 1 << variable_count
        full_mask = (1 << value_count) - 1
        # Bit i in a mask is the expression's value on assignment i. Boolean
        # operations on functions can therefore be computed as integer bit operations.
        expressions = {
            0: _ExpressionWithDepth(0, _ConstantExpression(False)),
            full_mask: _ExpressionWithDepth(0, _ConstantExpression(True)),
        }
        masks_by_depth: tp.List[tp.Set[_TruthTableMask]] = [
            set() for _ in range(maximum_depth + 1)
        ]
        masks_by_depth[0].update(expressions)

        for variable in range(variable_count):
            mask = sum(
                1 << assignment
                for assignment in range(value_count)
                if assignment & (1 << variable)
            )
            expressions[mask] = _ExpressionWithDepth(
                0,
                _LiteralExpression(variable, False),
            )
            expressions[full_mask ^ mask] = _ExpressionWithDepth(
                0,
                _LiteralExpression(variable, True),
            )
            masks_by_depth[0].update((mask, full_mask ^ mask))

        # Enumerate every new function obtainable at each exact gate depth. Keeping
        # only the first expression for a mask also keeps its minimum known depth.
        pool = list(masks_by_depth[0])
        for depth in range(1, maximum_depth + 1):
            for first_index, first_mask in enumerate(pool):
                first = expressions[first_mask]
                for second_mask in itertools.islice(pool, first_index, None):
                    second = expressions[second_mask]
                    if max(first.depth, second.depth) + 1 != depth:
                        continue
                    for operation, result in (
                        (_BinaryOperation.AND, first_mask & second_mask),
                        (_BinaryOperation.OR, first_mask | second_mask),
                    ):
                        if result in expressions:
                            continue
                        expressions[result] = _ExpressionWithDepth(
                            depth,
                            _BinaryExpression(
                                operation,
                                first.expression,
                                second.expression,
                            ),
                        )
                        masks_by_depth[depth].add(result)
            pool.extend(masks_by_depth[depth])

        self._expression_databases[cache_key] = expressions
        return expressions

    def _find_small_expression(
        self,
        mask: _TruthTableMask,
        variable_count: int,
        maximum_depth: int,
    ) -> tp.Optional[_Expression]:
        cache_key = (mask, variable_count, maximum_depth)
        if cache_key in self._expression_searches:
            return self._expression_searches[cache_key]

        complete_depth = min(maximum_depth, _COMPLETE_SEARCH_DEPTH)
        expressions = self._small_expression_database(
            variable_count,
            complete_depth,
        )
        if mask in expressions:
            result: tp.Optional[_Expression] = expressions[mask].expression
        elif maximum_depth <= complete_depth:
            result = None
        else:
            result = self._find_expression_from_database(
                mask,
                maximum_depth,
                expressions,
            )

        self._expression_searches[cache_key] = result
        return result

    @staticmethod
    def _find_expression_from_database(
        mask: _TruthTableMask,
        maximum_depth: int,
        expressions: tp.Dict[_TruthTableMask, _ExpressionWithDepth],
    ) -> tp.Optional[_Expression]:
        # An AND decomposition can only use supersets of the target mask; an OR
        # decomposition can only use subsets. Try the smaller candidate set first.
        supersets = [candidate for candidate in expressions if candidate & mask == mask]
        subsets = [candidate for candidate in expressions if candidate | mask == mask]
        searches = sorted(
            (
                (supersets, _BinaryOperation.AND),
                (subsets, _BinaryOperation.OR),
            ),
            key=lambda item: len(item[0]),
        )

        for candidates, operation in searches:
            for first_index, first_mask in enumerate(candidates):
                first = expressions[first_mask]
                for second_mask in itertools.islice(candidates, first_index, None):
                    second = expressions[second_mask]
                    if max(first.depth, second.depth) + 1 != maximum_depth:
                        continue
                    if operation is _BinaryOperation.AND:
                        result = first_mask & second_mask
                    else:
                        result = first_mask | second_mask
                    if result == mask:
                        return _BinaryExpression(
                            operation,
                            first.expression,
                            second.expression,
                        )
        return None

    def _add_gate(
        self,
        gate_type: GateType,
        operands: tuple[Label, ...] = (),
    ) -> Label:
        label = f"preparata_muller_{self._next_gate}"
        self._next_gate += 1
        self.circuit.emplace_gate(label, gate_type, operands)
        return label

    def _constant(self, value: bool) -> Label:
        if value in self._constants:
            return self._constants[value]
        if not self.inputs:
            label = self._add_gate(
                gate.ALWAYS_TRUE if value else gate.ALWAYS_FALSE,
            )
        else:
            gate_type = gate.OR if value else gate.AND
            label = self._add_gate(
                gate_type,
                (self.inputs[0], self.negated_inputs[0]),
            )
        self._constants[value] = label
        return label

    def _combine_balanced(
        self,
        labels: tp.Sequence[Label],
        gate_type: GateType,
    ) -> Label:
        if gate_type not in {gate.AND, gate.OR}:
            raise ValueError("Balanced trees are only supported for AND and OR gates")

        # Pair adjacent operands on every level to minimize the tree depth.
        current = list(labels)
        if not current:
            return self._constant(gate_type == gate.AND)
        while len(current) > 1:
            next_level = [
                self._add_gate(gate_type, (current[i], current[i + 1]))
                for i in range(0, len(current) - 1, 2)
            ]
            if len(current) % 2:
                next_level.append(current[-1])
            current = next_level
        return current[0]

    def _build_normal_form(
        self,
        truth_table: tp.Sequence[bool],
        variables: tp.Sequence[int],
    ) -> Label:
        if all(truth_table):
            return self._constant(True)
        if not any(truth_table):
            return self._constant(False)

        true_count = sum(truth_table)
        # Build DNF when true rows are scarcer, otherwise build CNF from false rows.
        use_dnf = true_count <= len(truth_table) - true_count
        inner_type = gate.AND if use_dnf else gate.OR
        outer_type = gate.OR if use_dnf else gate.AND
        terms = []

        for assignment, value in enumerate(truth_table):
            if value != use_dnf:
                continue
            literals = []
            for bit, variable in enumerate(variables):
                assignment_value = bool(assignment & (1 << bit))
                positive = assignment_value if use_dnf else not assignment_value
                literals.append(
                    self.inputs[variable] if positive else self.negated_inputs[variable]
                )
            terms.append(self._combine_balanced(literals, inner_type))

        return self._combine_balanced(terms, outer_type)

    def _materialize_expression(
        self,
        expression: _Expression,
        variables: tp.Sequence[int],
    ) -> Label:
        if isinstance(expression, _ConstantExpression):
            return self._constant(expression.value)
        if isinstance(expression, _LiteralExpression):
            variable = variables[expression.variable]
            if expression.negated:
                return self.negated_inputs[variable]
            return self.inputs[variable]
        gate_type = (
            gate.AND if expression.operation is _BinaryOperation.AND else gate.OR
        )
        first = self._materialize_expression(expression.left, variables)
        second = self._materialize_expression(expression.right, variables)
        return self._add_gate(gate_type, (first, second))

    def _build_exact(
        self,
        truth_table: tp.Sequence[bool],
        variables: tp.Sequence[int],
        maximum_depth: int,
    ) -> tp.Optional[Label]:
        mask = sum(
            1 << assignment for assignment, value in enumerate(truth_table) if value
        )
        expression = self._find_small_expression(
            mask,
            len(variables),
            maximum_depth,
        )
        if expression is None:
            return None
        return self._materialize_expression(expression, variables)

    @staticmethod
    def _choose_tail_size(input_size: int, maximum: int) -> tp.Optional[int]:
        for tail_size in range(1, maximum + 1):
            if input_size <= (1 << tail_size) + tail_size:
                return tail_size
        return None

    def _build_disjunctive(
        self,
        truth_table: tp.Sequence[bool],
        variables: tp.Sequence[int],
        tail_size: int,
        recurse: bool,
    ) -> Label:
        tail_size = min(tail_size, len(variables))
        prefix_size = len(variables) - tail_size
        if prefix_size == 0:
            if recurse:
                return self._build_recursive(truth_table, variables, False)
            return self._build_normal_form(truth_table, variables)

        # Apply Shannon expansion to the prefix variables. Each prefix minterm is
        # conjoined with the corresponding function on the remaining tail variables.
        cofactor_size = 1 << tail_size
        first_cofactor = [
            truth_table[tail_assignment << prefix_size]
            for tail_assignment in range(cofactor_size)
        ]
        if all(
            truth_table[prefix_assignment | (tail_assignment << prefix_size)]
            == first_cofactor[tail_assignment]
            for prefix_assignment in range(1 << prefix_size)
            for tail_assignment in range(cofactor_size)
        ):
            # All prefix assignments induce the same cofactor, so the function does
            # not depend on the prefix. Avoid rebuilding and joining identical tails.
            return self._build_recursive(
                first_cofactor,
                variables[prefix_size:],
                False,
            )

        terms = []
        for prefix_assignment in range(1 << prefix_size):
            prefix_literals = []
            for bit, variable in enumerate(variables[:prefix_size]):
                prefix_literals.append(
                    self.inputs[variable]
                    if prefix_assignment & (1 << bit)
                    else self.negated_inputs[variable]
                )
            prefix = self._combine_balanced(prefix_literals, gate.AND)
            cofactor = [
                truth_table[prefix_assignment | (tail_assignment << prefix_size)]
                for tail_assignment in range(cofactor_size)
            ]
            if recurse:
                suffix = self._build_recursive(
                    cofactor,
                    variables[prefix_size:],
                    False,
                )
            else:
                suffix = self._build_normal_form(
                    cofactor,
                    variables[prefix_size:],
                )
            terms.append(self._add_gate(gate.AND, (prefix, suffix)))

        return self._combine_balanced(terms, gate.OR)

    @staticmethod
    def _reconstruct_index(
        prefix_assignment: int,
        prefix_positions: tp.Sequence[int],
        tail_assignment: int,
        tail_positions: tp.Sequence[int],
    ) -> int:
        result = 0
        for bit, position in enumerate(prefix_positions):
            if prefix_assignment & (1 << bit):
                result |= 1 << position
        for bit, position in enumerate(tail_positions):
            if tail_assignment & (1 << bit):
                result |= 1 << position
        return result

    def _find_exact_tail(
        self,
        truth_table: tp.Sequence[bool],
        variable_count: int,
        tail_size: int,
        maximum_depth: int,
    ) -> tp.Optional[tp.Tuple[int, ...]]:
        if variable_count < tail_size:
            return None
        # Look for a tail whose every prefix cofactor has an exact expression within
        # the requested depth. Its position tuple is reused to build the partition.
        for tail_positions in itertools.combinations(range(variable_count), tail_size):
            tail_set = set(tail_positions)
            prefix_positions = [
                position
                for position in range(variable_count)
                if position not in tail_set
            ]
            for prefix_assignment in range(1 << len(prefix_positions)):
                mask = 0
                for tail_assignment in range(1 << tail_size):
                    index = self._reconstruct_index(
                        prefix_assignment,
                        prefix_positions,
                        tail_assignment,
                        tail_positions,
                    )
                    if truth_table[index]:
                        mask |= 1 << tail_assignment
                if self._find_small_expression(mask, tail_size, maximum_depth) is None:
                    break
            else:
                return tail_positions
        return None

    def _build_partition(
        self,
        truth_table: tp.Sequence[bool],
        variables: tp.Sequence[int],
        tail_positions: tp.Sequence[int],
        maximum_depth: int,
    ) -> Label:
        # Rebuild the same prefix/tail cofactors selected by _find_exact_tail and join
        # them as a disjunction of prefix-minterm/suffix-expression pairs.
        tail_set = set(tail_positions)
        prefix_positions = [
            position for position in range(len(variables)) if position not in tail_set
        ]
        suffix_variables = [variables[position] for position in tail_positions]
        terms = []

        for prefix_assignment in range(1 << len(prefix_positions)):
            prefix_literals = []
            for bit, position in enumerate(prefix_positions):
                variable = variables[position]
                prefix_literals.append(
                    self.inputs[variable]
                    if prefix_assignment & (1 << bit)
                    else self.negated_inputs[variable]
                )
            prefix = self._combine_balanced(prefix_literals, gate.AND)
            cofactor = [
                truth_table[
                    self._reconstruct_index(
                        prefix_assignment,
                        prefix_positions,
                        tail_assignment,
                        tail_positions,
                    )
                ]
                for tail_assignment in range(1 << len(tail_positions))
            ]
            suffix = self._build_exact(
                cofactor,
                suffix_variables,
                maximum_depth,
            )
            if suffix is None:
                suffix = self._build_normal_form(cofactor, suffix_variables)
            terms.append(self._add_gate(gate.AND, (prefix, suffix)))

        return self._combine_balanced(terms, gate.OR)

    def _build_recursive(
        self,
        truth_table: tp.Sequence[bool],
        variables: tp.Sequence[int],
        allow_recursive_cofactors: bool,
    ) -> Label:
        input_size = len(variables)
        if all(truth_table):
            return self._constant(True)
        if not any(truth_table):
            return self._constant(False)

        # At most two variables fit directly into a depth-optimal normal form.
        # For three variables, first try exhaustive exact synthesis at depth three.
        if input_size == _THREE_VARIABLE_TAIL_SIZE:
            exact = self._build_exact(
                truth_table,
                variables,
                _THREE_VARIABLE_TAIL_SIZE,
            )
            if exact is not None:
                return exact
            return self._build_normal_form(truth_table, variables)
        if input_size < _THREE_VARIABLE_TAIL_SIZE:
            return self._build_normal_form(truth_table, variables)

        # The Preparata--Muller split uses a tail of size s while n <= 2**s + s.
        # Try the largest exact tail first because it covers more input variables.
        if input_size <= (1 << _FOUR_VARIABLE_TAIL_SIZE) + _FOUR_VARIABLE_TAIL_SIZE:
            tail_positions = self._find_exact_tail(
                truth_table,
                input_size,
                _FOUR_VARIABLE_TAIL_SIZE,
                _FOUR_VARIABLE_TAIL_SIZE,
            )
            if tail_positions is not None:
                return self._build_partition(
                    truth_table,
                    variables,
                    tail_positions,
                    _FOUR_VARIABLE_TAIL_SIZE,
                )

        if input_size <= ((1 << _THREE_VARIABLE_TAIL_SIZE) + _THREE_VARIABLE_TAIL_SIZE):
            tail_positions = self._find_exact_tail(
                truth_table,
                input_size,
                _THREE_VARIABLE_TAIL_SIZE,
                _THREE_VARIABLE_TAIL_SIZE,
            )
            if tail_positions is not None:
                return self._build_partition(
                    truth_table,
                    variables,
                    tail_positions,
                    _THREE_VARIABLE_TAIL_SIZE,
                )

        tail_size = self._choose_tail_size(input_size, _MAX_DIRECT_TAIL_SIZE)
        if tail_size is not None:
            return self._build_disjunctive(
                truth_table,
                variables,
                tail_size,
                False,
            )

        if allow_recursive_cofactors:
            tail_size = self._choose_tail_size(input_size, _MAX_RECURSIVE_TAIL_SIZE)
            if tail_size is not None:
                return self._build_disjunctive(
                    truth_table,
                    variables,
                    tail_size,
                    True,
                )

        return self._build_normal_form(truth_table, variables)


def generate_circuit_pm1971(function: Function) -> Circuit:
    """
    Synthesize a circuit for a fully defined Boolean function.

    The generated circuit realizes ``function`` using two-input AND and OR gates and
    input negations. Constant gates are used only for functions without inputs. Input
    and output positions in the returned circuit have the same meaning and order as
    those in ``function``. Multi-output functions are supported.

    This generator follows the disjunctive construction introduced by Franco P.
    Preparata and David E. Muller in 1971. For practical input sizes, up to
    ``2**8 + 8`` inputs, its worst-case logic depth is ``n + 1``; larger functions use
    a fallback construction without that guarantee. It is intended for direct,
    solver-free synthesis when circuit depth is more important than circuit size. Its
    resource requirements grow exponentially with the number of inputs, as does the
    truth table consumed by the method.

    :param function: fully defined Boolean function to synthesize.
    :return: circuit equivalent to ``function``.

    """
    builder = _PreparataMullerBuilder(
        function.input_size,
        function.get_truth_table(),
    )
    return builder.circuit
