"""..."""

from flask import current_app


def parse_and_validate_list_params(args, allowed_sort_fields, default_sort_field):
    """
    Parses and validates pagination and sorting parameters from request.args.
    Returns a dictionary of valid parameters or a dictionary of error details.
    """

    params = {}

    # 1. Parse and Validate Pagination
    try:
        offset = int(args.get("offset", "0"))
        limit = int(args.get("limit", "20"))
    except ValueError:
        return None, {
            "message": "Query parameters 'limit' and 'offset' must be integers.",
            "status": 400,
        }

    max_offset = current_app.config["MAX_OFFSET"]
    if not 0 <= offset <= max_offset:
        return None, {
            "message": f"Offset has to be a positive number no greater than {max_offset}.",
            "status": 400,
        }

    max_limit = current_app.config["MAX_LIMIT"]
    if not (
        0 <= limit <= max_limit
    ):  # Note: A limit of 0 can be valid if you want to get just the count
        return None, {
            "message": f"Limit has to be a positive number no greater than {max_limit}.",
            "status": 400,
        }

    params["offset"] = offset
    params["limit"] = limit

    # 2. Parse and Validate Sorting
    sort_param = args.get(
        "sort", default_sort_field
    )  # if there is sort field use it, or sort will be equal to default sort field value
    sort_direction = 1  # Ascending by default

    if sort_param.startswith("-"):  # indicating descending
        sort_direction = -1
        sort_field = sort_param[1:]
    else:
        sort_field = sort_param

    if sort_field not in allowed_sort_fields:
        allowed = ", ".join(allowed_sort_fields)  # is allowed_sort_fields a list?
        return None, {
            "message": f"Invalid sort field '{sort_field}'. Allowed fields are: {allowed}",
            "status": 400,
        }

    params["sort_criteria"] = {sort_field: sort_direction}

    return params, None
