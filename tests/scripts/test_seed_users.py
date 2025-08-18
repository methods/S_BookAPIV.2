"""Test file for seeding database with user data"""

import json
from unittest.mock import mock_open, patch

import bcrypt

from app.extensions import mongo
from scripts.seed_users import main as seed_users_main
from scripts.seed_users import seed_users


def test_seed_users_successfully(test_app):
    """
    GIVEN an empty database and a list of user data
    WHEN the seed_users function is called
    THEN the users should be created in the database with hashed passwords.
    """
    # Arrange
    # define the user data we want to seed the database with
    sample_users = [
        {"email": "test.admin@example.com", "password": "AdminPassword123"},
        {"email": "test.user@example.com", "password": "UserPassword456"},
    ]

    # Enter application context and
    # Ensure the database is clean before the test
    with test_app.app_context():
        mongo.db.users.delete_many({})

        # Act: call the function we are testing
        result_message = seed_users(sample_users)

        # Check the database state directly
        assert mongo.db.users.count_documents({}) == 2
        admin_user = mongo.db.users.find_one({"email": "test.admin@example.com"})
        assert admin_user is not None

        # Verify the password was hashed
        assert admin_user["password"] != "AdminPassword123"
        assert bcrypt.checkpw(
            b"AdminPassword123", admin_user["password"].encode("utf-8")
        )
    assert "Successfully seeded 2 users" in result_message


def test_seed_users_skips_if_user_already_exists(test_app, capsys):
    """
    GIVEN a database that already contains one user
    WHEN the seed_users function is called with a list containing that existing user and a new one
    THEN it should skip the existing user, insert the new one, and print a skip message.
    """
    # Arrange
    users_to_attempt_seeding = [
        {"email": "existing.user@example.com", "password": "Password123"},
        {"email": "new.user@example.com", "password": "Password456"},
    ]

    with test_app.app_context():
        # start with a clean state
        mongo.db.users.delete_many({})

        mongo.db.users.insert_one(
            {
                "email": "existing.user@example.com",
                "password_hash": "some-pre-existing-hash",
            }
        )
        # ACT
        result_message = seed_users(users_to_attempt_seeding)

        # Assert
        final_count = mongo.db.users.count_documents({})
        assert final_count == 2
        # Check the return message from the function
        assert "Successfully seeded 1 users" in result_message

        # Check the print
        captured = capsys.readouterr()
        assert "Skipping existing user: existing.user@example.com" in captured.out
        assert "Created user: new.user@example.com" in captured.out


def test_main_runs_seeding_process_successfully(capsys):
    """
    GIVEN a successful file read
    WHEN the main function is called
    THEN it should call seed_users with the loaded data and print success messages.
    """
    # Arrange
    fake_json_data = '[{"email": "fake@user.com", "password": "fakepass"}]'

    # Create mock objects for all of main's dependencies
    with patch("scripts.seed_users.create_app"), patch(
        "scripts.seed_users.seed_users"
    ) as mock_seed_users, patch("builtins.open", mock_open(read_data=fake_json_data)):

        # Act
        seed_users_main()

        # Assert
        expected_data = json.loads(fake_json_data)
        mock_seed_users.assert_called_once_with(expected_data)
        # Did it print the right message?
        captured = capsys.readouterr()
        assert "--- Starting user seeding ---" in captured.out
        assert "--- Seeding complete ---" in captured.out


def test_main_throws_filenotfounderror(capsys):
    """
    GIVEN the data file does not exist
    WHEN the main function is called
    THEN it should print a FileNotFoundError message and not call seed_users.
    """
    # Arrange
    with patch("scripts.seed_users.create_app"), patch(
        "scripts.seed_users.seed_users"
    ) as mock_seed_users, patch("builtins.open") as mock_file:

        mock_file.side_effect = FileNotFoundError

        # Act
        seed_users_main()

        # Assert
        captured = capsys.readouterr()
        assert "Error: Data file not found at" in captured.out

        mock_seed_users.assert_not_called()


def test_main_throws_jsondecodeerror(capsys):
    """
    GIVEN the data file contains invalid JSON
    WHEN the main function is called
    THEN it should print a JSONDecodeError message and not call seed_users.
    """
    # Arrange
    corrupted_json_data = (
        '{"email": "bad@user.com", "password": "badpass"'  # Missing closing brace
    )

    with patch("scripts.seed_users.create_app"), patch(
        "scripts.seed_users.seed_users"
    ) as mock_seed_users, patch(
        "builtins.open", mock_open(read_data=corrupted_json_data)
    ):

        # Act
        seed_users_main()

        # Assert
        captured = capsys.readouterr()
        assert "Error: Could not decode JSON from" in captured.out
        mock_seed_users.assert_not_called()
