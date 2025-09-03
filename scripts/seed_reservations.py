"""
Script for populating reservations to a database
"""
import json
import os
import sys

# upload sample data json to be used
def load_reservations_json():
    """Loads the reservation seed data from the JSON file
    located at scripts/test_data/sample_reservations.json
    Returns:
        list: List of reservation dictionaries
    """
    try:
        script_dir = os.path.dirname(__file__)
        data_path = os.path.join(script_dir, "test_data/sample_reservations.json")

        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Data file not found at '{data_path}'.", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from '{data_path}'. Check for syntax.", file=sys.stderr) # pylint: disable=line-too-long
        return None


if __name__ == "__main__":
    print(load_reservations_json())
