from boolean_circuit_tool.core.python_function import PyFunction


f = PyFunction(lambda xs: [sum(xs) % 2], input_size=4)
print(f.is_monotone())

g = PyFunction.from_int_binary_func(lambda x, y: x + y, input_int_len=2, output_int_len=3)
print(g.is_symmetric())
