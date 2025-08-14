"""Seeding user_data script"""

import json
import os

import bcrypt

from app import create_app
from app.extensions import mongo


def seed_users(users_to_seed: list) -> str:
    """
    Processes a list of user data, hashes their passwords,
    and inserts them into the database. Skips existing users.

    This function MUST be run within an active Flask application context.

    Args:
        users_to_seed: A list of dicts, each with 'email' and 'password'.

    Returns:
        A string summarizing the result.
    """
    count = 0

    for user_data in users_to_seed:
        email = user_data["email"]

        # Check if data already exists
        if mongo.db.users.find_one({"email": email}):
            print(f"Skipping existing user: {email}")
            continue

        # hash the password
        hashed_password = bcrypt.hashpw(
            user_data["password"].encode("utf-8"), bcrypt.gensalt()
        )

        # insert to new user
        mongo.db.users.insert_one(
            {"email": email, "password_hash": hashed_password.decode("utf-8")}
        )
        count += 1
        print(f"Created user: {email}")

    return f"Successfully seeded {count} users"


def main():
    """
    Main execution function to run the seeding process.
    handles app context, data loading, and calls the core seeding logic.
    """
    # Create the DEVELOPMENT app when run from the command line
    app = create_app()
    with app.app_context():

        # 1. Get the directory where THIS script (seed_users.py) lives.
        script_dir = os.path.dirname(__file__)

        # 2. Build the full, absolute path to the JSON file.
        user_data_path = os.path.join(script_dir, "test_data/sample_user_data.json")

        try:
            # You can define your default users here or import from another file
            with open(user_data_path, "r", encoding="utf-8") as user_file:
                default_users = json.load(user_file)

            print("--- Starting user seeding ---")

            message = seed_users(default_users)
            print(f"--- {message} ---")
            print("--- Seeding complete ---")

        except FileNotFoundError:
            print(f"Error: Data file not found at '{user_data_path}'.")
        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from '{user_data_path}'. Check for syntax errors."
            )


if __name__ == "__main__":
    main()
