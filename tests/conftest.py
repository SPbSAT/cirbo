import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--db-verify",
        action="store_true",
        default=False,
        help="run tests to verify the correctness of the database",
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
    config.addinivalue_line("markers", "db: mark test as related to database")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--db-verify"):
        return
    skip_db_checks = pytest.mark.skip(reason="need --db-verify option to run")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip_db_checks)
