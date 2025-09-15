"""..."""

from flask import request

from app.validators import parse_and_validate_list_params


def test_validator_with_defaults(test_app):
    """Test that the validator returns correct defaults when no params are given."""

    with test_app.test_request_context("/books"):
        params, error = parse_and_validate_list_params(
            request.args,
            allowed_sort_fields=["title", "author"],
            default_sort_field="title",
        )
        assert error is None
        assert params["offset"] == 0
        assert params["limit"] == 20
        assert params["sort_criteria"] == {"title": 1}


def test_validator_with_valid_sort(test_app):
    """Test parsing of a valid ascending and descending sort parameter."""

    # Test ascending
    with test_app.test_request_context("/books?sort=author"):
        params, error = parse_and_validate_list_params(
            request.args, ["title", "author"], "title"
        )
        assert error is None
        assert params["sort_criteria"] == {"author": 1}

    # Test descending
    with test_app.test_request_context("/books?sort=-title"):
        params, error = parse_and_validate_list_params(
            request.args, ["title", "author"], "title"
        )
        assert error is None
        assert params["sort_criteria"] == {"title": -1}


def test_validator_with_invalid_sort_field(test_app):
    """Test that an invalid sort field returns a 400 error."""

    with test_app.test_request_context("/books?sort=year"):
        params, error = parse_and_validate_list_params(
            request.args, ["title", "author"], "title"
        )
        assert params is None
        assert error is not None
        assert error["status"] == 400
        assert "Invalid sort field 'year'" in error["message"]
