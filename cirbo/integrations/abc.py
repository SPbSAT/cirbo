import dataclasses
import typing as tp

from cirbo.core import Circuit
from cirbo.exceptions import CirboError

__all__ = [
    'ABCUnavailableError',
    "ABCCommand",
    "abc_transform",
]


class ABCUnavailableError(CirboError):
    """Raised when an ABC mutation is used without the native ABC extension."""

    pass


@dataclasses.dataclass(frozen=True)
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
        return dataclasses.replace(self, name=name)


def _join_scripts(*scripts: str) -> str:
    return "; ".join(
        script.strip().rstrip(";").strip() for script in scripts if script.strip()
    )


def abc_transform(ckt: Circuit, cmd: tp.Union[str, ABCCommand]) -> Circuit:
    """
    Transform a Boolean circuit using ABC.

    :param ckt: The input boolean circuit to be transformed.
    :param cmd: The command to be executed by the ABC tool
    :return: The transformed boolean circuit after processing by the ABC tool

    """
    try:
        from abc_wrapper import run_abc_commands_c
    except ImportError as exc:
        raise ABCUnavailableError(
            "ABC support is not available in this Cirbo installation"
        ) from exc

    script = cmd.script if isinstance(cmd, ABCCommand) else cmd

    bench = ckt.into_bench().format_circuit()
    bench = run_abc_commands_c(bench, script)
    return Circuit.from_bench_string(bench)
