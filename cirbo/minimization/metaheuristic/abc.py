"""ABC-based mutations for the metaheuristic circuit optimizer."""

import importlib
import random
import typing as tp

from extensions.abc_wrapper.src.abc import ABCCommand

from cirbo.core.circuit import Circuit
from .exceptions import ABCUnavailableError
from .mutation import CircuitMutation

__all__ = [
    'ABCHeavyMutation',
    'ABCHeavyMutation',
    "DEEPSYN",
    "REWIRE",
    "DC2",
    "IF",
    "MFS",
    "ORCHESTRATE",
    "ABC_HEAVY_COMMANDS",
]


DEEPSYN = ABCCommand("deepsyn", "&get; &deepsyn -I 1 -J 1; &put;")
REWIRE = ABCCommand("rewire", "rewire -I 5; b;")
DC2 = ABCCommand("dc2", "dc2; b;")
IF = ABCCommand("if", "if -g -K 6 -C 8; b;")
MFS = ABCCommand("mfs", "if; mfs2; strash;")
ORCHESTRATE = ABCCommand("orchestrate", "orchestrate; b; orchestrate;")

ABC_HEAVY_COMMANDS: tuple[ABCCommand, ...] = (
    DEEPSYN,
    REWIRE,
    DC2,
    IF,
    MFS,
    ORCHESTRATE,
)


def _get_abc_transform() -> tp.Callable[[Circuit, str], Circuit]:
    """Return the bridge only when the optional native extension is present."""
    try:
        importlib.import_module('abc_wrapper')
        from extensions.abc_wrapper.src.abc import abc_transform
    except ImportError as exc:
        raise ABCUnavailableError(
            'ABC mutations require the abc_wrapper extension. Build Cirbo without '
            'DISABLE_ABC_CEXT enabled.'
        ) from exc
    return abc_transform


class _ABCMutation(CircuitMutation):
    """
    Shared implementation for a random mutation based on the ABC command set.

    Each time a mutation is invoked, a random ABC command from the internal class-level
    list is performed on the circuit, and the result is returned.

    """

    _commands: tuple[ABCCommand, ...]

    def __init__(self):
        self._last_command: tp.Optional[str] = None

    @property
    def last_command(self) -> tp.Optional[str]:
        """Command selected during the most recent mutation execution, if any."""
        return self._last_command

    def mutate(self, circuit: Circuit, rng: random.Random) -> Circuit:
        """Run one randomly selected ABC command on the ``circuit``."""
        command = "strash;" + rng.choice(self._commands).script
        self._last_command = command
        return _get_abc_transform()(circuit, command)


class ABCHeavyMutation(_ABCMutation):
    """Apply one randomly selected restructure ABC command."""

    _commands = ABC_HEAVY_COMMANDS
