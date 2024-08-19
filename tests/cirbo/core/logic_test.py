import pytest

from cirbo.core.logic import DontCare, DontCareCastError


def test_dont_care_raises_when_casted_to_bool():
    with pytest.raises(DontCareCastError):
        _ = bool(DontCare)
