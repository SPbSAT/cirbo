"""ABC-based mutations for the metaheuristic circuit optimizer."""

import importlib
import random
import typing as tp

from cirbo.core.circuit import Circuit
from .exceptions import ABCUnavailableError
from .mutation import CircuitMutation

__all__ = [
    'ABC_EASY_COMMANDS',
    'ABC_HARD_COMMANDS',
    'ABCEasyMutation',
    'ABCHardMutation',
]


ABC_EASY_COMMANDS: tuple[str, ...] = (
    'resyn; resyn; ps;',
    'resyn2; resyn2; ps;',
    'resyn2a; resyn2a; ps;',
    'resyn3; resyn3; ps;',
    'orchestrate; b; orchestrate; ps;',
    'dc2; b; ps',
    'if -g -K 6 -C 8; b; ps',
    'c2rs; b; ps',
    'r2rs; b; ps',
)

ABC_HARD_COMMANDS: tuple[str, ...] = ABC_EASY_COMMANDS + (
    'rewire -I 20; b; ps',
    '&get; &deepsyn -I 1 -J 20; &put; ps',
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

    Each time mutation is invoked a random ABC command from the internal class-level
    list is performed on the circuit and result is returned.

    """

    _commands: tuple[str, ...]

    def __init__(self):
        self._last_command: tp.Optional[str] = None

    @property
    def last_command(self) -> tp.Optional[str]:
        """Command selected during the most recent mutation execution, if any."""
        return self._last_command

    def mutate(self, circuit: Circuit, rng: random.Random) -> Circuit:
        """Run one randomly selected ABC command on the ``circuit``."""
        command = rng.choice(self._commands)
        self._last_command = command
        return _get_abc_transform()(circuit, command)


class ABCEasyMutation(_ABCMutation):
    """Apply one randomly selected low-cost ABC simplification command."""

    _commands = ABC_EASY_COMMANDS


class ABCHardMutation(_ABCMutation):
    """Apply one randomly selected higher-effort ABC simplification command."""

    _commands = ABC_HARD_COMMANDS
