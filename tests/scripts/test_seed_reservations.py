"""..."""

import json
from unittest.mock import MagicMock, mock_open, patch
import pytest

from scripts.seed_reservations import load_reservations_json, run_reservation_population
from scripts import seed_reservations as load_reservations_module


def test_load_reservations_json_success():
    """
    GIVEN a valid JSON string representing reservation data
    WHEN load_reservations_json is called with a mock of the file system
    THEN it should return the parsed data as a list of dictionaries.
    """
    # Arrange
    test_reservations_data = """[
        {
        "book_title": "To Kill a Mockingbird",
        "user_identifier": "user_harper_l",
        "state": "reserved"
    },
    {
        "book_title": "Pride and Prejudice",
        "user_identifier": "user_jane_a",
        "state": "cancelled"
    }
    ]"""

    # use mock_open to simulate reading this valid content
    mocked_file = mock_open(read_data=test_reservations_data)

    with patch("builtins.open", mocked_file):

        # Act
        reservations = load_reservations_json()
        # Assert
        assert isinstance(reservations, list)
        assert len(reservations) == 2

        assert reservations[0]["book_title"] == "To Kill a Mockingbird"
        assert reservations[0]["user_identifier"] == "user_harper_l"
        assert reservations[0]["state"] == "reserved"
        assert reservations[-1]["book_title"] == "Pride and Prejudice"
        assert reservations[-1]["user_identifier"] == "user_jane_a"
        assert reservations[-1]["state"] == "cancelled"


def test_load_reservation_file_not_found(capsys):
    """
    GIVEN that the reservation data file is not found on the file system
    WHEN load_reservations_json is called
    THEN the function should return None and print a 'file not found' error message to stderr.
    """
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_reservations_json()

        assert result is None
        captured = capsys.readouterr()
        assert "ERROR: Data file not found" in captured.err


def test_load_reservations_json_decode_error(capsys):
    """
    GIVEN that the reservation data file contains invalid (malformed) JSON
    WHEN load_reservations_json is called
    THEN the function should handle the JSONDecodeError, 
    return None, and print a helpful error message to stderr.
    """
    bad_json = '{"broken": }'  # invalid JSON
    m = mock_open(read_data=bad_json)
    # patch builtins.open so json.load() raises JSONDecodeError inside function
    with patch("builtins.open", m):
        result = load_reservations_json()

    assert result is None
    captured = capsys.readouterr()
    assert "Could not decode JSON" in captured.err


def test_load_reservations_integration_reads_file(tmp_path, monkeypatch):
    """
    Integration: create a temporary scripts/test_data/sample_reservations.json
    and monkeypatch module __file__ so load_reservations_json resolves to that path.
    """
    # Prepare temporary dir structure
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    test_data_dir = scripts_dir / "test_data"
    test_data_dir.mkdir()
    # IMPORTANT: create the exact filename the function expects
    file_path = test_data_dir / "sample_reservations.json"

    sample_data = [{"reservation_id": "r1", "status": "active"}]
    file_path.write_text(json.dumps(sample_data), encoding="utf-8")

    # Monkeypatch the module's __file__ so os.path.dirname(__file__) -> scripts_dir
    fake_module_file = scripts_dir / "seed_reservations.py"
    monkeypatch.setattr(load_reservations_module, "__file__", str(fake_module_file))

    # Call the function — it should read the created file
    result = load_reservations_json()
    assert result == sample_data

# -------------- TESTS for run_reservation_population -----------------

# A list of test cases for the failure scenarios
error_scenarios = [
    # id is a descriptive name that will appear in the test results
    pytest.param([], [{"user_id": 1}], id="book_collection_is_empty"),
    pytest.param([{"id": 1}], None, id="reservation_collection_is_none"),
    pytest.param([], [], id="both_collections_are_empty"),
    pytest.param(None, None, id="both_collections_are_none"),
]
@pytest.mark.parametrize(
    "mock_books_return_val, mock_reservations_return_val",
    error_scenarios
)
@patch("scripts.seed_reservations.get_book_collection")
@patch("scripts.seed_reservations.get_reservation_collection")
def test_returns_404_if_any_collection_is_missing(
    mock_get_books, mock_get_reservations, # Mocks come first
    test_app, # fixture from conftest.py
    mock_books_return_val, mock_reservations_return_val # Params come after
):
    """
    GIVEN that either the book or reservation collection is missing (falsy)
    WHEN run_reservations_population is called
    THEN it should return a 404 error with a specific message
    """
    # ARRANGE: Use the parameters to set the return values of our mocks
    mock_get_books.return_value = mock_books_return_val
    mock_get_reservations.return_value = mock_reservations_return_val

    # ACT
    with test_app.app_context():
        response, status_code = run_reservation_population()

    # ASSERT: The expected outcome is the same for all parametrized cases
    assert status_code == 404
    assert response.get_json() == {"error": "Required collections could not be loaded."}

    # You can also assert that the first function was always called
    mock_get_books.assert_called_once()


def test_returns_200_when_collections_are_present(test_app, mongo_setup, sample_book_data):
    """
    GIVEN a database with books and reservations
    WHEN run_reservations_population is called
    THEN it should return a 200 success response
    """
    # ARRANGE: Use the fixtures to seed the mock database with data.
    # The `mongo_setup` fixture ensures the collections are clean.
    _ = mongo_setup

    sample_reservations = [
        {"user_id": "user123", "book_id": "550e8400-e29b-41d4-a716-446655440000"}
    ]

    with test_app.app_context():
        # Get the collections from the GLOBAL `mongo` object
        from app.extensions import mongo # pylint: disable=import-outside-toplevel
        mongo.db.books.insert_many(sample_book_data)
        mongo.db.reservations.insert_many(sample_reservations)

        # ACT: Call the function. It will now read from the mongomock db.
        response, status_code = run_reservation_population()

        # ASSERT
        assert status_code == 200
        assert response.get_json()["status"] == "success"
