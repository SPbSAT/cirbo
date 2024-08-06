import dummy_extension


def test_add():
    assert dummy_extension.add(5, 3) == 8
    assert dummy_extension.subtract(10, 3) == 7
