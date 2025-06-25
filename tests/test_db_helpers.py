# pylint: disable=missing-docstring

from utils.db_helpers import load_books_json

def test_can_load_books_json():
    books = load_books_json()
    print(books)
    assert isinstance(books, list)
    assert "title" in books[0]
