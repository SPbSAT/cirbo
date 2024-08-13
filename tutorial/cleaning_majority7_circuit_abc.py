from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
from boolean_circuit_tool.core.circuit import Circuit
from abc_wrapper import run_abc_commands


ckt = Circuit.bare_circuit(7)
lbls = add_sum_n_bits(ckt, ckt.inputs, basis='AIG')
ckt.set_outputs([lbls[-1]])
ckt_after_abc_str = run_abc_commands(ckt.into_bench().format_circuit(), 'strash; dc2')
ckt_after_abc = Circuit.from_bench_string(ckt_after_abc_str)
