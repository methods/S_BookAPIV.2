# pylint: disable=line-too-long
"""Tests for reservation service layer functions."""

from unittest.mock import patch

from bson import ObjectId

from app.services.reservation_services import (count_reservations_for_book,
                                               fetch_reservations_for_book)


@patch("app.services.reservation_services.mongo")
def test_count_reservations_for_book(mock_mongo, test_app):
    """
    WHEN count_reservations_for_book is called with a book_id
    THEN it should call count_documents on the reservations collection
    WITH the correct filter
    """
    # Arrange
    book_id_obj = ObjectId()
    mock_mongo.db.reservations.count_documents.return_value = 5

    with test_app.app_context():
        # ACT
        result = count_reservations_for_book(book_id_obj)

    # Assert
    assert result == 5
    mock_mongo.db.reservations.count_documents.assert_called_once_with(
        {"book_id": book_id_obj}
    )


# Plan: Write unit tests that mock the .aggregate method
# the tests will not check the data returned, instead will inspect the pipeline argument that is passed to aggregate to ensure it's constructed properly based on the book_id, offset, and limit provided
# KEY PRINCIPLE- we are not testing if MongoDB can perform an aggregation- we trust it can.
# we are testing that our function correctly builds the list of instructions (the pipeline) that we send to MongoDB.
# THEREFORE: our test's most important job is to "capture" the pipeline variable that the function creates
# and assert that its contents are exactly what we expect.


@patch("app.services.reservation_services.mongo")
def test_fetch_reservations_for_book_builds_pipeline_with_defaults(
    mock_mongo, test_app
):
    """
    GIVEN a book_id is provided
    WHEN fetch_reservations_for_book is called with no offset or limit
    THEN it should call the aggregate method with a correctly structured pipeline,
    using the default offset of 0 and limit of 20.
    """
    # ARRANGE
    book_id_obj = ObjectId()
    # The actual data returned doesn't matter for this test, only the call itself.
    mock_mongo.db.reservations.aggregate.return_value = []

    with test_app.app_context():
        # ACT: Call the function with only the required argument
        fetch_reservations_for_book(book_id_obj)

    # ASSERT
    # 1. Ensure the aggregate method was called exactly once.
    mock_mongo.db.reservations.aggregate.assert_called_once()

    # 2. Capture the arguments that were passed to the aggregate method.
    # call_args is a tuple: (args, kwargs). The pipeline is the first positional arg.
    actual_pipeline = mock_mongo.db.reservations.aggregate.call_args[0][0]

    # 3. Verify the structure and content of the pipeline.
    assert isinstance(actual_pipeline, list)
    assert len(actual_pipeline) == 5  # We expect 5 stages in our pipeline

    # Check the critical stages
    assert actual_pipeline[0] == {"$match": {"book_id": book_id_obj}}
    assert actual_pipeline[3] == {"$skip": 0}  # Default value
    assert actual_pipeline[4] == {"$limit": 20}  # Default value


@patch("app.services.reservation_services.mongo")
def test_fetch_reservations_for_book_builds_pipeline_with_custom_params(
    mock_mongo, test_app
):
    """
    GIVEN a book_id, a custom offset, and a custom limit
    WHEN fetch_reservations_for_book is called
    THEN it should call the aggregate method with a pipeline that reflects
    those custom pagination values.
    """
    # ARRANGE
    book_id_obj = ObjectId()
    mock_mongo.db.reservations.aggregate.return_value = []
    custom_offset = 10
    custom_limit = 5

    with test_app.app_context():
        # ACT: Call the function with custom pagination arguments
        fetch_reservations_for_book(
            book_id_obj, offset=custom_offset, limit=custom_limit
        )

    # ASSERT
    mock_mongo.db.reservations.aggregate.assert_called_once()
    actual_pipeline = mock_mongo.db.reservations.aggregate.call_args[0][0]

    # Verify the custom values are in the correct stages
    assert actual_pipeline[0] == {"$match": {"book_id": book_id_obj}}
    assert actual_pipeline[3] == {"$skip": custom_offset}  # Custom value
    assert actual_pipeline[4] == {"$limit": custom_limit}  # Custom value
