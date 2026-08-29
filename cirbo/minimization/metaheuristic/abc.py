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
    'b; rewrite; rewrite -z; b; rewrite -z; b; b; rewrite; rewrite -z; b; rewrite -z; b;',  # alias is "resyn; resyn;"
    (
        'b; rewrite; refactor; b; rewrite; rewrite -z; b; refactor -z; rewrite -z; b; b; rewrite; refactor; b; '
        'rewrite; rewrite -z; b; refactor -z; rewrite -z; b;'
    ),  # alias is "resyn2; resyn2;"
    (
        'b; rewrite; b; rewrite; rewrite -z; b; rewrite -z; b; b; rewrite; b; rewrite; rewrite -z; b; rewrite -z; b;'
    ),  # alias is "resyn2a; resyn2a;"
    (
        'b; resub; resub -K 6; b; resub -z; resub -z -K 6; b; resub -z -K 5; b; b; resub; resub -K 6; b; '
        'resub -z; resub -z -K 6; b; resub -z -K 5; b;'
    ),  # alias is "resyn3; resyn3;"
    'orchestrate; b; orchestrate;',
    'dc2; b',
    'if -g -K 6 -C 8; b',
    (
        'b -l; resub -K 6 -l; rewrite -l; resub -K 6 -N 2 -l; refactor -l; resub -K 8 -l; b -l; resub -K 8 -N 2 -l; '
        'rewrite -l; resub -K 10 -l; rewrite -z -l; resub -K 10 -N 2 -l; b -l; resub -K 12 -l; refactor -z -l; '
        'resub -K 12 -N 2 -l; rewrite -z -l; b -l; b'
    ),  # alias is "c2rs; b"
    (
        'b; resub -K 6; rewrite; resub -K 6 -N 2; refactor; resub -K 8; b; resub -K 8 -N 2; rewrite; resub -K 10; '
        'rewrite -z; resub -K 10 -N 2; b; resub -K 12; refactor -z; resub -K 12 -N 2; rewrite -z; b; b'
    ),  # alias is "r2rs; b"
)

ABC_HARD_COMMANDS: tuple[str, ...] = ABC_EASY_COMMANDS + (
    'rewire -I 20; b',
    '&get; &deepsyn -I 1 -J 20; &put',
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

    # FIXME: consequent ABC mutations mustn't cause overhead on from-to cribo Circuit and "strash;" abuse.
    #        So, maybe, need to add a folding step after mutations sequence is generated.

    def mutate(self, circuit: Circuit, rng: random.Random) -> Circuit:
        """Run one randomly selected ABC command on the ``circuit``."""
        command = "strash;" + rng.choice(self._commands)
        self._last_command = command
        return _get_abc_transform()(circuit, command)


class ABCEasyMutation(_ABCMutation):
    """Apply one randomly selected low-cost ABC simplification command."""

    _commands = ABC_EASY_COMMANDS


class ABCHardMutation(_ABCMutation):
    """Apply one randomly selected higher-effort ABC simplification command."""

    _commands = ABC_HARD_COMMANDS
