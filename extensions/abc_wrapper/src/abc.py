from dataclasses import dataclass, replace

from cirbo.core import Circuit

try:
    from abc_wrapper import run_abc_commands_c
except ImportError:
    pass


__all__ = [
    "abc_transform",
    "ABCCommand",
]


@dataclass(frozen=True, slots=True)
class ABCCommand:
    """
    Named ABC command or a sequence of ABC commands.

    Supports composition using the `>>` operator.

    Example: DEEPSYN >> REWIRE >> DC2
    """

    name: str
    script: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ABC command name must not be empty")
        if not self.script.strip():
            raise ValueError("ABC command script must not be empty")

    def __rshift__(self, other: "ABCCommand") -> "ABCCommand":
        """Sequentially compose two ABC commands."""
        if not isinstance(other, ABCCommand):
            return NotImplemented

        return ABCCommand(
            name=f"({self.name} + {other.name})",
            script=_join_scripts(self.script, other.script),
        )

    def named(self, name: str) -> "ABCCommand":
        """Give this command (or pipeline) another name."""
        return replace(self, name=name)


def _join_scripts(*scripts: str) -> str:
    return "; ".join(
        script.strip().rstrip(";").strip() for script in scripts if script.strip()
    )


def abc_load_circuit(ckt: Circuit, cmd: str | ABCCommand) -> Circuit:
    """
    Loads a Boolean circuit into ABC memory.

    :param ckt: The input boolean circuit to be transformed.
    :param cmd: The command to be executed by the ABC tool
    :return: The transformed boolean circuit after processing by the ABC tool
    """
    script = cmd.script if isinstance(cmd, ABCCommand) else cmd

    bench = ckt.into_bench().format_circuit()
    bench = run_abc_commands_c(bench, script)
    return Circuit.from_bench_string(bench)


def abc_transform(ckt: Circuit, cmd: str | ABCCommand) -> Circuit:
    """
    Transform a Boolean circuit using ABC.

    :param ckt: The input boolean circuit to be transformed.
    :param cmd: The command to be executed by the ABC tool
    :return: The transformed boolean circuit after processing by the ABC tool
    """
    script = cmd.script if isinstance(cmd, ABCCommand) else cmd

    bench = ckt.into_bench().format_circuit()
    bench = run_abc_commands_c(bench, script)
    return Circuit.from_bench_string(bench)
