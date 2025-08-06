"""Tests for auth/JWT upgrade"""

import bcrypt

from app import mongo


def test_register_with_valid_data(client, users_db_setup):
    """GIVEN a clean users collection
    WHEN a POST request is sent to /auth/register with new user data
    THEN the repsonse should be 201 CREATED and the user should exist in the DB"""
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    new_user_data = {"email": "newuser@example.com", "password": "a-secure-password"}
    # ACT
    response = client.post("/auth/register", json=new_user_data)

    # Verify the user was actually created in the database
    assert response.status_code == 201
    user_in_db = mongo.db.users.find_one({"email": "newuser@example.com"})
    assert user_in_db is not None
    assert "password_hash" in user_in_db
    # You can even check if the password hashes match!
    assert bcrypt.checkpw(
        b"a-secure-password", user_in_db["password_hash"].encode("utf-8")
    )


def test_register_with_duplicate_email(client, users_db_setup):
    """
    GIVEN a user already exists in the database
    WHEN a POST request is sent to /auth/register with the same email
    THEN the response should be 409 Conflict"""
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    existing_user_data = {
        "email": "newuser@example.com",
        "password": "a-secure-password",
    }
    client.post("/auth/register", json=existing_user_data)
    # sanity-check
    user_in_db = mongo.db.users.find_one({"email": "newuser@example.com"})
    assert user_in_db is not None
    assert "password_hash" in user_in_db

    # Act: try to register with the same email again
    response = client.post("/auth/register", json=existing_user_data)

    # Assert
    assert response.status_code == 409
    assert "email is already registered" in response.get_json()["message"].lower()

def test_register_fails_with_empty_json(client, users_db_setup):
    """
    When a POST is sent with an empty JSON,
    it returns a 400 and an error message
    """
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    json_body = ""

    # Act
    response = client.post(
        "/auth/register", 
        json=json_body,
        content_type="application/json"
    )

    assert response.status_code == 400
    assert "request body cannot be empty" in response.get_json()["error"].lower()

def test_request_fails_with_invalid_json(client, users_db_setup):
    """
    When a POST is sent with an empty JSON,
    it returns a 400 and an error message
    """
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    invalid_json_string = "this is not json"

    # Act
    response = client.post(
        "/auth/register", data=invalid_json_string,
        content_type="application/json"
    )

    assert response.status_code == 400
    assert "invalid json format" in response.get_json()["message"].lower()
