import subprocess
import tempfile
import time
import configparser

from boolean_circuit_tool.core.circuit import Circuit

config = configparser.RawConfigParser()
config.read('config.cfg')
path_to_abc = dict(config.items('ABC'))["path_to_abc"]


def construct_command(command_list):
    """
    Constructs one command line from several commands, separating them with ;
    """
    return "; ".join(command_list)


def read_command(filename):
    return f"read {filename}"


def write_command(filename):
    return f"write {filename}"


def run_command(command, tl=None):
    process = subprocess.Popen(
        path_to_abc,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    start_time = time.time()
    out, _ = process.communicate(input=command, timeout=tl)
    exec_time = round(time.time() - start_time, 5)
    process.kill()
    return out, exec_time


def simplify(input_path, output_path, tl=None):
    command = construct_command(
        [
            read_command(input_path),
            "strash",
            "dc2",
            "drw",
            "rewrite",
            "refactor",
            "resub",
            write_command(output_path),
        ]
    )
    out, _ = run_command(command, tl)
    return out


def fraig(input_path, output_path, tl=None):
    command = construct_command(
        [
            read_command(input_path),
            "strash",
            "fraig",
            write_command(output_path),
        ]
    )
    return run_command(command, tl)


def simplify_with_abc(circuit: Circuit) -> Circuit:

    with tempfile.NamedTemporaryFile(suffix='.bench', delete=True) as tmp:
        circuit.save_to_file(tmp.name)
        out = simplify(tmp.name, tmp.name)
        # TODO: handle `out`
        ckt_simp = Circuit.from_bench(tmp.name)

    return ckt_simp

