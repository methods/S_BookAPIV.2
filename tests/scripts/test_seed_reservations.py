"""..."""

import json
from unittest.mock import mock_open, patch

from scripts.seed_reservations import load_reservations_json
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
