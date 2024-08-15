from boolean_circuit_tool.core import Circuit

try:
    from abc_wrapper import run_abc_commands_c
except ImportError:
    pass


def abc_transform(ckt: Circuit, cmd: str) -> Circuit:
    """
    Transforms a given boolean circuit by invoking the ABC tool with a specified command.

    :param ckt: The input boolean circuit to be transformed.
    :param cmd: The command string to be executed by the ABC tool
    :return: The transformed boolean circuit after processing by the ABC tool
    """

    bch = ckt.into_bench().format_circuit()
    bch = run_abc_commands_c(bch, cmd)
    ckt = Circuit.from_bench_string(bch)
    return ckt
