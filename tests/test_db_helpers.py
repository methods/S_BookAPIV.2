# pylint: disable=missing-docstring
from unittest.mock import patch, mock_open
import json
import pytest
from utils.db_helpers import load_books_json

def test_can_load_books_json():
    books = load_books_json()
    print(books)
    assert isinstance(books, list)
    assert "title" in books[0]

def test_load_books_raises_error_if_file_not_found():
    # Arrange:
    with patch("builtins.open") as mock_file:
        mock_file.side_effect = FileNotFoundError("File not found at path")

    # Act and Assert:
    # Use 'pytest.raises' as a context manager to check that the
    # expected expectation is raised inside the 'with' block
        with pytest.raises(FileNotFoundError) as excinfo:
            load_books_json()

        assert "File not found" in str(excinfo.value)

def test_load_books_raises_decodeerror_for_invalid_json(capsys):
    # Arrange:
    # A string representing a broken JSON file (missing closing brace)
    mock_file_content = '''{
        "id": "550e8400-e29b-41d4-a716-446655440000"
    '''

    # Use mock_open to simulate reading our broken JSON string
    # The read_data parameter pre-populates the content that 'read()' will return
    m = mock_open(read_data=mock_file_content)

    # Patch 'open' used in the module under test
    with patch("builtins.open", m):
        # Act and Assert
        with pytest.raises(json.JSONDecodeError):
            load_books_json()

    captured = capsys.readouterr()
    assert "Failed to decode JSON" in captured.out
