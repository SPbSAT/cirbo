import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--db-xaig-verify",
        action="store_true",
        default=False,
        help="run tests to verify the correctness of the xaig database",
    )
    parser.addoption(
        "--db-aig-verify",
        action="store_true",
        default=False,
        help="run tests to verify the correctness of the aig database",
    )
    parser.addoption(
        "--db-xaig-path",
        action="store",
        default="./xaig_db.bin",
        help="Path to the xaig database file",
    )
    parser.addoption(
        "--db-aig-path",
        action="store",
        default="./aig_db.bin",
        help="Path to the aig database file",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "db_xaig: mark test as related to xaig database")
    config.addinivalue_line("markers", "db_aig: mark test as related to aig database")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--db-xaig-verify"):
        skip_db_checks = pytest.mark.skip(reason="need --db-xaig-verify option to run")
        for item in items:
            if "db_xaig" in item.keywords:
                item.add_marker(skip_db_checks)
    if not config.getoption("--db-aig-verify"):
        skip_db_checks = pytest.mark.skip(reason="need --db-aig-verify option to run")
        for item in items:
            if "db_aig" in item.keywords:
                item.add_marker(skip_db_checks)
