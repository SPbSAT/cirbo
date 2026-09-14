import pytest

# Package can be compiled without ABC extension when
# environment variable DISABLE_ABC_CEXT=1 is set.
#
try:
    from abc_wrapper import run_abc_commands_c
except ImportError:
    pass


@pytest.mark.ABC
def test_run_abc_commands():
    assert callable(run_abc_commands_c)
