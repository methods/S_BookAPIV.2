# MongoDB Data Management Scripts

## Overview

This directory contains command-line scripts for managing the data in your MongoDB collections. These tools are designed to help developers quickly set up a uniform, clean environment for testing and development by populating and clearing data.

- **create_books.py**: Populates the books collection from scripts/test_data/books.json.
- **delete_books.py**: Performs a hard delete of all documents from the books collection.
- **create_reservations**.py: Populates the reservations collection from scripts/test_data/reservations.json, linking them to existing books.
- **delete_reservations.py**: Performs a hard delete of all documents from the reservations collection.
- **seed_users.py**: Populates the users collection with initial data for authentication.

All deletion scripts include a confirmation prompt to prevent accidental data loss. All creation scripts use an "upsert" operation, meaning they will update existing records or insert new ones, preventing duplicates.

---

## Prerequisites

Before running these scripts, please ensure you have the following installed and running:

1.  **Make**: The `make` command must be available in your shell.
2.  **Python 3.x**: The scripts are written in Python 3.
3.  **A running MongoDB instance**: The scripts will fail if they cannot connect to a database. By default, they connect to `mongodb://localhost:27017/`.

---


## Usage

The recommended way to manage the database is by using the Makefile located in the project's root directory. These commands handle the virtual environment and Python paths for you.

### Step 1: Install Dependencies

If you haven't already, install all required Python packages into a local virtual environment. This command only needs to be run once.

```bash
make install
```

### Step 2: Manage the Database with Make

Once installed, you can use the following commands to manage the database state.

| Command | Description |
|---------------------|-----------------------------------------------------------------------------|
| make setup | (Recommended) Resets the entire database and seeds all data. |
| make clean-db | Deletes ALL books and reservations. |
| make books | Populates the books collection. |
| make reservations | Populates the reservations collection. |
| make seed-users | Populates the users collection. |

---

For a complete refresh of your development environment, simply run:
```bash
make setup
```


## Running Scripts Directly (Advanced)

If you need to run a script individually without using make, you can execute it directly. Ensure your virtual environment is active (source venv/bin/activate).

All commands must be run from the **root directory** of the project.

**Note**: Setting PYTHONPATH=. is crucial. It tells Python to include the current directory in its search path, allowing the scripts to import modules from the main app.

### Book Scripts

**To delete all books**:
(You will be asked to confirm this destructive action.)

```bash
PYTHONPATH=. python scripts/delete_books.py
```

**To create/update books:**
```bash
PYTHONPATH=. python scripts/create_books.py
```

### Reservation Scripts

**To delete all reservations**:
(You will be asked to confirm this destructive action.)

```bash
PYTHONPATH=. python scripts/delete_reservations.py
```

**To create/update reservations:**
```bash
PYTHONPATH=. python scripts/seed_reservations.py
```

**Note:** (Note: The reservation creation script is named seed_reservations.py)