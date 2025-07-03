# pylint: disable=missing-docstring
from unittest.mock import patch, mock_open
import json
import pytest
from utils.db_helpers import load_books_json

def test_load_books_json_successfully():

    # Arrange
    test_books_data = '''[
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "title": "Pride and Prejudice",
            "synopsis": "A romantic novel about the relationship between Elizabeth Bennet and Mr. Darcy.",
            "author": "Jane Austen",
            "links": {
            "self": "/books/550e8400-e29b-41d4-a716-446655440003",
            "reservations": "/books/550e8400-e29b-41d4-a716-446655440003/reservations",
            "reviews": "/books/550e8400-e29b-41d4-a716-446655440003/reviews"
            },
            "state": "active"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440004",
            "title": "The Catcher in the Rye",
            "synopsis": "A story about teenage rebellion and alienation.",
            "author": "J.D. Salinger",
            "links": {
            "self": "/books/550e8400-e29b-41d4-a716-446655440004",
            "reservations": "/books/550e8400-e29b-41d4-a716-446655440004/reservations",
            "reviews": "/books/550e8400-e29b-41d4-a716-446655440004/reviews"
            },
            "state": "active"
        }
    ]'''
    # use mock_open to simulate reading this valid content
    mocked_file = mock_open(read_data=test_books_data)

    with patch("builtins.open", mocked_file):

        # Act
        books = load_books_json()
        # Assert
        assert isinstance(books, list)
        assert len(books) == 2

        assert books[0]["title"] == "Pride and Prejudice"
        assert books[-1]["title"] == "The Catcher in the Rye"

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
    m = mock_open(read_data=mock_file_content)

    # Patch 'open' used in the module under test
    # When 'open()' is called, use this fake file
    with patch("builtins.open", m):
        # Act and Assert
        with pytest.raises(json.JSONDecodeError):
            load_books_json()

    captured = capsys.readouterr()
    assert "Failed to decode JSON" in captured.out


def test_integration_load_books_json():
    books = load_books_json()

    assert isinstance(books, list)
    assert isinstance(books[0], dict)
    assert "title" in books[0]
