# pylint: disable=missing-docstring

# this test should check resource is in db
# resource that it will be adding is the resource from sample_books.json
# to import .json file i need to ...?
# it is also an integration test so needs fixtures at the top
# check the integration test file form before

from scripts.create_books import load_books_json

def test_can_load_books_json():
    books = load_books_json()
    print(books)
    assert isinstance(books, list)
    assert "title" in books[0]
