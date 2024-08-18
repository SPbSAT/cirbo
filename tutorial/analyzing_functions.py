from cirbo.core import PyFunction, TruthTable


f = PyFunction(lambda xs: [sum(xs) % 2], 4)
print(f.is_monotone())

g = PyFunction.from_int_binary_func(
    lambda x, y: x + y, 2, 3)
print(g.is_symmetric())

e = TruthTable(['1101'])
print(e.is_constant())
