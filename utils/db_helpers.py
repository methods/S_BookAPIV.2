"""
Module for creating books and loading sample book data.
"""

import json
import os


def load_books_json():
    """
    Load and return sample book data from scripts/test_data/sample_books.json.
    Returns:
        list: List of book dictionaries.
    """
    # Get the absolute path from this file to the project root
    root_dir = os.path.dirname(os.path.dirname(__file__))

    # Build absolute path to the books.json file
    json_path = os.path.join(root_dir, "scripts", "test_data", "sample_books.json")

    try:
        # Load and return the JSON data
        with open(json_path, "r", encoding="utf-8") as file:
            books = json.load(file)

        return books
    except FileNotFoundError as e:
        # Catch the specific error and re-raise it
        print(f"Error: The file at {json_path} was not found")
        raise e
    except json.JSONDecodeError as e:
        print(
            f"Error: Failed to decode JSON from {json_path}. The file may be corrupt."
        )
        raise e
