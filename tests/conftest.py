from cirbo.circuits_db.data_utils import DEFAULT_AIG_DB_PATH, DEFAULT_XAIG_DB_PATH


def pytest_addoption(parser):
    parser.addoption(
        "--db-xaig-path",
        action="store",
        default=DEFAULT_XAIG_DB_PATH,
        help="Path to the xaig database file",
    )
    parser.addoption(
        "--db-aig-path",
        action="store",
        default=DEFAULT_AIG_DB_PATH,
        help="Path to the aig database file",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "db_xaig: mark test as related to xaig database")
    config.addinivalue_line("markers", "db_aig: mark test as related to aig database")
