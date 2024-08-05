import random

import pytest
from boolean_circuit_tool.circuits_db.db import CircuitsDatabase
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.truth_table import TruthTableModel
from boolean_circuit_tool.synthesis.circuit_search import Basis, CircuitFinderSat

from tests.synthesis.circuit_search_test import check_correctness


def generate_random_truth_table():
    table = [''.join(random.choice('01') for _ in range(8)) for _ in range(3)]
    while table[0] == table[1] or table[1] == table[2] or table[0] == table[2]:
        table = [''.join(random.choice('01') for _ in range(8)) for _ in range(3)]
    return table


random.seed(1448)
truth_tables = [generate_random_truth_table() for _ in range(100)]


@pytest.fixture(scope="module")
def db_xaig_connection(pytestconfig):
    """
    Fixture for setting up the XAIG database connection for the test module.

    Parameters:
    pytestconfig (Config): The pytest configuration object, used to get
    the --db-xaig-path option.

    Yields:
    CircuitsDatabase: An instance of the CircuitsDatabase connected to the specified path.
    """
    path_to_db = pytestconfig.getoption("--db-xaig-path")
    with CircuitsDatabase(path_to_db) as db:
        yield db


@pytest.fixture(scope="module")
def db_aig_connection(pytestconfig):
    """
    Fixture for setting up the AIG database connection for the test module.

    Parameters:
    pytestconfig (Config): The pytest configuration object, used to get
    the --db-aig-path option.

    Yields:
    CircuitsDatabase: An instance of the CircuitsDatabase connected to the specified path.
    """
    path_to_db = pytestconfig.getoption("--db-aig-path")
    with CircuitsDatabase(path_to_db) as db:
        yield db


@pytest.mark.db
@pytest.mark.parametrize("tt_str", truth_tables)
def test_synthesis_db_xaig(tt_str, db_xaig_connection):
    ttm = TruthTableModel(tt_str)
    ckt_from_db: Circuit = db_xaig_connection.get_by_raw_truth_table_model(
        ttm.get_model_truth_table()
    )
    circuit_finder = CircuitFinderSat(
        ttm, ckt_from_db.elements_number - 3, basis=Basis.XAIG
    )
    circuit_from_synthesis = circuit_finder.find_circuit()
    check_correctness(circuit_from_synthesis, tt_str, hasdontcares=True)
    check_correctness(ckt_from_db, tt_str, hasdontcares=True)

    # with pytest.raises(NoSolutionError):
    #     circuit_finder_2 = CircuitFinderSat(
    #         ttm, ckt_from_db.elements_number - 4, basis=Basis.XAIG
    #     )
    #     circuit_finder_2.find_circuit()


@pytest.mark.db
@pytest.mark.parametrize("tt_str", truth_tables)
def test_synthesis_db_aig(tt_str, db_aig_connection):
    ttm = TruthTableModel(tt_str)
    ckt_from_db: Circuit = db_aig_connection.get_by_raw_truth_table_model(
        ttm.get_model_truth_table()
    )
    circuit_finder = CircuitFinderSat(
        ttm, ckt_from_db.elements_number - 3, basis=Basis.AIG
    )
    circuit_from_synthesis = circuit_finder.find_circuit()
    check_correctness(circuit_from_synthesis, tt_str, hasdontcares=True)
    check_correctness(ckt_from_db, tt_str, hasdontcares=True)

    # with pytest.raises(NoSolutionError):
    #     circuit_finder_2 = CircuitFinderSat(
    #         ttm, ckt_from_db.elements_number - 4, basis=Basis.XAIG
    #     )
    #     circuit_finder_2.find_circuit()
