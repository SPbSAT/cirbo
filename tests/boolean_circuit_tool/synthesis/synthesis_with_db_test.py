import random

import pytest
from boolean_circuit_tool.circuits_db.db import CircuitsDatabase
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.truth_table import TruthTableModel
from boolean_circuit_tool.synthesis.circuit_search import Basis, CircuitFinderSat
from boolean_circuit_tool.synthesis.exception import NoSolutionError, SolverTimeOutError

from tests.boolean_circuit_tool.synthesis.circuit_search_test import check_correctness


def are_complement(tt1, tt2):
    for c1, c2 in zip(tt1, tt2):
        if not (c1 == '*' or c2 == '*' or c1 != c2):
            return False
    return True


def generate_random_truth_table(w0=0.5, w1=0.5, w2=0.0):
    choices = ['0', '1', '*']

    tt = [''.join(random.choices(choices, [w0, w1, w2], k=8)) for _ in range(3)]
    while (
        are_complement(tt[0], tt[1])
        or are_complement(tt[1], tt[2])
        or are_complement(tt[0], tt[2])
    ):
        tt = [''.join(random.choices(choices, [w0, w1, w2], k=8)) for _ in range(3)]
    return tt


random.seed(1448)
truth_tables = [generate_random_truth_table() for _ in range(100)]
truth_tables_with_dontcares = [
    generate_random_truth_table(0.4, 0.4, 0.2) for _ in range(100)
]


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
@pytest.mark.parametrize("tt_str", truth_tables + truth_tables_with_dontcares)
def test_synthesis_vs_db_xaig(tt_str, db_xaig_connection):
    ttm = TruthTableModel(tt_str)
    ckt_from_db: Circuit = db_xaig_connection.get_by_raw_truth_table_model(
        ttm.get_model_truth_table()
    )
    circuit_finder = CircuitFinderSat(
        ttm, ckt_from_db.elements_number, basis=Basis.XAIG
    )
    circuit_from_synthesis = circuit_finder.find_circuit()
    check_correctness(circuit_from_synthesis, tt_str, hasdontcares=True)
    check_correctness(ckt_from_db, tt_str, hasdontcares=True)

    with pytest.raises(NoSolutionError):
        circuit_finder_2 = CircuitFinderSat(
            ttm, ckt_from_db.elements_number - 1, basis=Basis.XAIG
        )
        circuit_finder_2.find_circuit()


@pytest.mark.db
@pytest.mark.parametrize("tt_str", truth_tables + truth_tables_with_dontcares)
def test_synthesis_vs_db_aig(tt_str, db_aig_connection):
    ttm = TruthTableModel(tt_str)
    ckt_from_db: Circuit = db_aig_connection.get_by_raw_truth_table_model(
        ttm.get_model_truth_table()
    )
    circuit_finder = CircuitFinderSat(ttm, ckt_from_db.elements_number, basis=Basis.AIG)
    circuit_from_synthesis = circuit_finder.find_circuit()
    check_correctness(circuit_from_synthesis, tt_str, hasdontcares=True)
    check_correctness(ckt_from_db, tt_str, hasdontcares=True)

    with pytest.raises((NoSolutionError, SolverTimeOutError)):
        circuit_finder_2 = CircuitFinderSat(
            ttm, ckt_from_db.elements_number - 1, basis=Basis.AIG
        )
        circuit_finder_2.find_circuit(time_limit=2)


@pytest.mark.db
@pytest.mark.parametrize("tt_str", truth_tables[:5] + truth_tables_with_dontcares[:5])
def test_synthesis_with_db(tt_str, db_xaig_connection):
    ttm = TruthTableModel(tt_str)
    ckt_from_db: Circuit = db_xaig_connection.get_by_raw_truth_table_model(
        ttm.get_model_truth_table()
    )
    circuit_finder = CircuitFinderSat(
        ttm, ckt_from_db.elements_number, basis=Basis.XAIG
    )
    circuit_from_synthesis = circuit_finder.find_circuit(circuit_db=db_xaig_connection)
    assert ckt_from_db.format_circuit() == circuit_from_synthesis.format_circuit()
