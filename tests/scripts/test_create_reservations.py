"""..."""
import json
from unittest.mock import mock_open, patch
import pytest

from scripts.seed_reservations import load_reservations_json


def test_load_reservations_json_success():
    """..."""
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
