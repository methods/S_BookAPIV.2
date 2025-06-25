"""
Module for creating books and loading sample book data.
"""

import json
import os

def load_books_json():
    """
    Load and return sample book data from scripts/test_data/sample_books.json.
    Returns:
        list: List of book dictionaries."""
    # Get the absolute path from this file to the project root
    root_dir = os.path.dirname(os.path.dirname(__file__))
    print('rootDIR', root_dir)

    # Build absolute path to the books.json file
    json_path = os.path.join(root_dir, 'scripts', 'test_data', 'sample_books.json')
    print('json_PATH', json_path)

    # Load and return the JSON data
    with open(json_path, 'r', encoding='utf-8') as file:
        books = json.load(file)
        print(books)
    return books
