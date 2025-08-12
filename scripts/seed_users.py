""" Seeding user_data script"""

import bcrypt
from app.extensions import mongo

def seed_users(users_to_seed: list) -> str:
    """
    Processes a list of user data, hashes their passwords,
    and inserts them into the database. Skips existing users.
    
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
            user_data["password"].encode("utf-8"),
            bcrypt.gensalt()
        )

        # insert to new user
        mongo.db.users.insert_one({
            "email": email,
            "password_hash": hashed_password.decode("utf-8")
        })
        count += 1
        print(f"Created user: {email}")

    return f"Successfully seeded {count} users"
