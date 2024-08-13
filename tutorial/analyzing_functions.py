from boolean_circuit_tool.core.python_function import PyFunction


f = PyFunction(lambda *xs: [sum(xs) % 2])
print(f.is_monotone())

g = PyFunction.from_int_binary_func(2, 3, lambda x, y: x + y)
print(g.is_symmetric())
