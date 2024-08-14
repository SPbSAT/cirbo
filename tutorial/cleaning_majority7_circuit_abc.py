from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum_n_bits
from boolean_circuit_tool.core.circuit import Circuit
from abc_wrapper import run_abc_commands


ckt = Circuit.bare_circuit(input_size=7)
*_, lst = add_sum_n_bits(ckt, ckt.inputs, basis='AIG')
ckt.mark_as_output(lst)
bch = ckt.into_bench().format_circuit()
bch = run_abc_commands(bch, 'strash; dc2')
ckt = Circuit.from_bench_string(bch)
