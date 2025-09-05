"""
Tests for the delete_reservations.py script functionality.

This file contains unit and integration tests for reservation deletion,
error handling, and output verification for the delete_reservations.py script.
"""

from unittest.mock import MagicMock, patch

from flask import Flask
from pymongo.errors import ConnectionFailure

from scripts.delete_reservations import delete_all_reservations, main


def test_delete_all_reservations_clears_collection_and_returns_count():
    """
    Unit test for delete_all_reservations: ensure it returns deleted_count
    when the collection.delete_many() result has deleted_count.
    """
    # Arrange: make a fake result object with deleted_count attribute
    fake_result = MagicMock()
    fake_result.deleted_count = 3

    # Fake collection with delete_many returning fake_result
    fake_collection = MagicMock()
    fake_collection.delete_many.return_value = fake_result

    # Act
    deleted_count = delete_all_reservations(fake_collection)

    # Assert
    assert deleted_count == 3
    fake_collection.delete_many.assert_called_once_with({})


@patch(
    "scripts.delete_reservations.delete_all_reservations",
    side_effect=ConnectionFailure("Mock DB connection error"),
)
def test_light_integration_main_handles_connection_failure_gracefully(
    mock_delete_all_reservations, capsys
):
    """
    Light integration test that relies on the REAL create_app() and get_reservation_collection()
    Verifies the essentials: exit code, stderr output, no stdout
    """
    # ACT
    exit_code = main()

    # ASSERT
    assert exit_code == 1
    mock_delete_all_reservations.assert_called_once()

    captured = capsys.readouterr()
    # Assert that the normal output (stdout) is empty.
    assert captured.out == ""
    # We assert that our specific error messages were printed to stderr.
    assert "❌ ERROR: Could not connect to MongoDB." in captured.err
    assert "Mock DB connection error" in captured.err


@patch(
    "scripts.delete_reservations.delete_all_reservations",
    side_effect=ConnectionFailure("Mock DB connection error"),
)
@patch("scripts.delete_reservations.get_reservation_collection")
@patch("scripts.delete_reservations.create_app")
def test_unit_main_handles_connection_failure_gracefully(
    mock_create_app,
    mock_get_reservation_collection,
    mock_delete_all_reservations,
    capsys,
):
    """
    Fully isolated UNIT test:
    Patch delete_all_reservations to raise ConnectionFailure. Ensure main() catches it,
    prints the error message to stderr, and returns exit code 1.
    """
    # Arrange: create a real Flask app stub for context manager
    mock_create_app.return_value = Flask(__name__)
    # make get_reservation_collection return a mock collection (not used because delete_all raises)
    mock_get_reservation_collection.return_value = MagicMock()

    # Act
    exit_code = main()

    # Assert return code
    assert exit_code == 1
    mock_delete_all_reservations.assert_called_once()

    captured = capsys.readouterr()
    # stdout should be empty on failure
    assert captured.out == ""
    # stderr should include the error header and details
    assert "❌ ERROR: Could not connect to MongoDB." in captured.err
    assert "Mock DB connection error" in captured.err


@patch("scripts.delete_reservations.delete_all_reservations", return_value=2)
@patch("scripts.delete_reservations.get_reservation_collection")
@patch("scripts.delete_reservations.create_app")
def test_main_success_prints_message_and_returns_zero(
    mock_create_app,
    mock_get_reservation_collection,
    mock_delete_all_reservations,  # unused argument
    capsys,
):
    """
    When delete_all_reservations returns > 0 we should print success to stdout and exit 0.
    """
    mock_create_app.return_value = Flask(__name__)
    mock_get_reservation_collection.return_value = MagicMock()

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "✅ Success: Removed 2 reservation(s)." in captured.out
    assert captured.err == ""
    mock_delete_all_reservations.assert_called_once()


@patch("scripts.delete_reservations.delete_all_reservations", return_value=0)
@patch("scripts.delete_reservations.get_reservation_collection")
@patch("scripts.delete_reservations.create_app")
def test_main_info_when_zero_returns_zero_and_prints_info(
    mock_create_app,
    mock_get_reservation_collection,
    mock_delete_all_reservations,
    capsys,
):
    """
    When delete_all_reservations returns 0 we should print the informational message and return 0.
    """
    mock_create_app.return_value = Flask(__name__)
    mock_get_reservation_collection.return_value = MagicMock()

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert (
        "ℹ️ Info: The collection was already empty. No reservations were deleted."
        in captured.out
    )  # pylint: disable=line-too-long
    assert captured.err == ""
    mock_delete_all_reservations.assert_called_once()
