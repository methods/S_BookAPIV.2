"""Service layer for handling book-related operations."""

from app.utils.helper import append_hostname
from app.datastore.mongo_db import get_book_collection
from app.datastore.mongo_helper import find_books

def fetch_active_books():
    """
    Fetches a cursor for all non-deleted books from the database.
    Returns a Python list.
    """

    collection = get_book_collection()
    query_filter = {"state": {"ne": "deleted"}}  # Only non-deleted books

    return list(find_books(collection, query_filter=query_filter))


def format_books_for_api(books, host_url):
    """
    Validate and format a list or cursor of raw book dicts for API response.

    Returns:
        tuple: (formatted_list, None) on success,
               (None, msg_lines) on validation failure.
    """

    required_fields = ["id", "title", "synopsis", "author", "links"]
    missing_fields_info = []

    # 1) Collect all validation errors
    for raw in books:
        missing = [f for f in required_fields if f not in raw]
        if missing:
            missing_fields_info.append(
                {"book": raw, "missing_fields": missing}
            )

    # 2) If any errors, build error message and return
    if missing_fields_info:
        msg_lines_list = ["Missing required fields:"]

        # In a loop, add new strings to the list
        for info in missing_fields_info:
            fields = ", ".join(info["missing_fields"])
            msg_lines_list.append(f"- {fields} in book: {info['book']}")

            # Join all the strings in the list ONCE at the end
            error_message = "\n".join(msg_lines_list)

            # 4. Return the final string
            return None, error_message


    # FORMAT: Remove fields not meant for the public API
    formatted_list = []
    for raw in books:
        book = raw.copy()
        book.pop("_id", None)
        book.pop("state", None)

        # Call the helper with the host_url it needs
        book_with_hostname = append_hostname(book, host_url)
        formatted_list.append(book_with_hostname)

    return formatted_list
