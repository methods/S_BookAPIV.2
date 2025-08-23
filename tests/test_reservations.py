# pylint: disable=redefined-outer-name
"""..."""
from datetime import datetime, timedelta, timezone
from bson.objectid import ObjectId
import pytest
import jwt
from app.extensions import mongo

# ------------------- FILE SPECIFIC FIXTURES -----------------
@pytest.fixture
def client_with_book(test_app):
    """
    Provides a test client,
    sets up the DB and
    ensures the database is clean and
    seeded with a single book for reservation tests.
    """
    with test_app.app_context():
        mongo.db.books.delete_many({})
        mongo.db.reservations.delete_many({})
        mongo.db.books.insert_one({
            "_id": ObjectId("5f8f8b8b8b8b8b8b8b8b8b8b"),
            "title": "Test Book"
        })

    yield test_app.test_client()

    # Teardown: Clean up the database
    with test_app.app_context():
        mongo.db.books.delete_many({})
        mongo.db.reservations.delete_many({})


@pytest.fixture(scope="function")
def auth_token(client_with_book):
    """
    GIVEN a test client
    WHEN this fixture is used
    THEN a valid JWT and Authorization header are generated.
    """
    # Section 1: Get the app context and secret key
    app = client_with_book.application
    secret_key = app.config.get('SECRET_KEY', 'default-secret-key-for-dev')

    # Section 2: Define the token's payload
    # This payload should mimic what your real login endpoint would create.
    # It includes who the user is and when the token expires.
    fake_user_id = str(ObjectId())
    payload = {
        'sub': fake_user_id,
        'iat': datetime.now(timezone.utc),  # Issued at
        'exp': datetime.now(timezone.utc) + timedelta(minutes=15) # Expiration time
    }

    # Section 3: Encode the token and create the header
    # PyJWT's encode function creates the token string.
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    # The HTTP header must be in the format 'Bearer <token>'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    return headers

#            ------------------ TESTS -----------------------

@pytest.mark.parametrize("payload, expected_message",
    [
        ("invalid!!", "Invalid Book ID"),
    ]
)
def test_reservation_with_invalid_book_id(
    payload,
    expected_message,
    client_with_book,
    auth_token
    ):
    """
    GIVEN a Flask app with a pre-existing book in the mock DB
    WHEN a POST request is made to /books/<book_id>/reservations without a book_id_str argument
    THEN a 400 status code is returned.
    """
    _ = client_with_book

    # Act
    response = client_with_book.post(
        f'/books/{payload}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"},
        headers=auth_token

    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == expected_message

@pytest.mark.parametrize("post_args, expected_status, expected_message",
    [
        ({}, 415, "Unsupported Media Type"),
        ({"json": {}}, 400, "Request body must be a non-empty JSON object"),
        ({"data": 'null', "content_type": 'application/json'}, 400, "Request body must be a non-empty JSON object"), # pylint: disable=line-too-long
        ({"data": '{ "bad" json }', "content_type": 'application/json'}, 400, "Invalid JSON format"),# pylint: disable=line-too-long
    ]
)
def test_create_reservation_with_bad_payload(
    post_args,
    expected_status,
    expected_message,
    client_with_book,
    auth_token
):
    """
    GIVEN a Flask app with a pre-existing book
    WHEN a POST request is made with no payload, an empty payload, a null payload, or invalid JSON
    THEN the correct error status code and message are returned.
    """
    _ = client_with_book
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"
    url = f'/books/{book_id}/reservations'

    # Combine the authorization headers with the arguments for this specific test case
    # The ** operator unpacks the dictionaries into keyword arguments
    request_kwargs = {**post_args, "headers": auth_token}

    # Act
    response = client_with_book.post(url, **request_kwargs)

    # Assert
    assert response.status_code == expected_status

    data = response.get_json()
    if response.status_code == 415:
        # Flask's default 415 error message uses a 'name' field
        assert data["error"]["name"] == expected_message
    else:
        error_message = data.get("message") or data.get("error")
        assert error_message == expected_message


def test_reservation_for_nonexistant_book(client_with_book):
    """
    GIVEN a FLASK APP WITH A PRE-EXISTING BOOK
    WHEN a POST request is made with a valid but non-existent book ID
    THEN a 404 Not Found statu sis returned
    """
    _ = client_with_book
    non_existent_id = ObjectId()

    response = client_with_book.post(
        f'/books/{non_existent_id}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"}
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data is not None

def test_create_reservation_success(client_with_book):
    """
    GIVEN a Flask app with a pre-existing book in the mock DB
    WHEN a POST request is made to /books/<book_id>/reservations with valid data
    THEN a 201 status code is returned with the new reservation data
    """
    _ = client_with_book
    # Arrange
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"

    # Act
    response = client_with_book.post(
        f'/books/{book_id}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['state'] == 'reserved'
    assert data['user']['forenames'] == 'Firstname'
    assert data['user']['surname'] == 'Tester'


FORENAMES_ERROR = "forenames is required and must be a string"
SURNAME_ERROR = "surname is required and must be a string"
@pytest.mark.parametrize("_test_name, payload, expected_messages",
    [
        (
            "forename is missing",
            {"surname": "Tester"},
            {"forenames": FORENAMES_ERROR}
        ),
        (
            "surname is missing",
            {"forenames": "John"},
            {"surname": SURNAME_ERROR}
        ),
        (
            "forename is wrong type (integer)",
            {"forenames": 12345, "surname": "Tester"},
            {"forenames": FORENAMES_ERROR}
        ),
        (
            "surname is wrong type (list)",
            {"forenames": "John", "surname": ["Doe"]},
            {"surname": SURNAME_ERROR}
        ),
        (
            "both fields are missing",
            {"some_other_field": "irrelevant"},
            {"forenames": FORENAMES_ERROR, "surname": SURNAME_ERROR}
        ),
        (
            "both fields are wrong type",
            {"forenames": None, "surname": True},
            {"forenames": FORENAMES_ERROR, "surname": SURNAME_ERROR}
        )
    ]
)
def test_create_reservation_with_invalid_data_fields(
    _test_name,
    payload,
    expected_messages,
    client_with_book
):
    """
    GIVEN a Flask app with a pre-existing book
    WHEN a POST request is made with missing or malformed data fields
    THEN a 400 status code is returned with a specific validation error message.
    """
    _ = client_with_book
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"
    url = f'/books/{book_id}/reservations'

    # Act: Send the invalid payload to the endpoint
    response = client_with_book.post(url, json=payload)

    # Assert
    assert response.status_code == 400
    data = response.get_json()
    # Check the overall error structure
    assert data["error"] == "Validation failed"
    assert data["messages"] == expected_messages
