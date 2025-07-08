# MongoDB Data Management Scripts

## Overview

This directory contains two command-line scripts for managing the 'books' collection in a MongoDB database. These tools are designed to help developers quickly set up a uniform, clean environment for testing and development.

-   **`delete_books.py`**: A script to perform a hard delete of all documents from the books collection. It includes a confirmation prompt to prevent accidental data loss.
-   **`create_books.py`**: A script that reads a local `books.json` file and populates the database, ensuring data uniformity by replacing existing books or inserting new ones (an "upsert" operation).

---

## Prerequisites

Before running these scripts, please ensure you have the following installed and running:

1.  **Make**: The `make` command must be available in your shell.
2.  **Python 3.x**: The scripts are written in Python 3.
3.  **A running MongoDB instance**: The scripts will fail if they cannot connect to a database. By default, they connect to `mongodb://localhost:27017/`.

---


## Usage

The recommended way to manage the project and database is by using the `Makefile` located in the project's root directory.

### Step 1: Install Dependencies

First, install all required Python packages into a local virtual environment. This command only needs to be run once.

```bash
make install
```

### Step 2: Manage the Database with Make

Once installed, you can use the following commands to manage the database state.
| Command       | Description                                                                                   |
|---------------|-----------------------------------------------------------------------------------------------|
| `make db-setup` | (Recommended) Resets the database. Runs `db-clean` and then `db-seed` for a full refresh.   |
| `make db-seed`  | Populates the database with the contents of `scripts/books.json`.                           |
| `make db-clean` | Runs the `delete_books.py` script to clear all documents from the 'books' collection.       |

---
## Running Scripts Directly (Advanced)

If you need to run the scripts without using make, you can execute them directly. Ensure you have installed the dependencies (pip install -r requirements.txt) and that your virtual environment is active.

From the **root directory** of the project, run the following:

**To delete all books**:
(You will be asked to confirm this destructive action.)

```bash
PYTHONPATH=. python scripts/delete_books.py
```

**To create/update the books:**
```bash
PYTHONPATH=. python scripts/create_books.py
```

**Note:** Setting PYTHONPATH=. is crucial. It tells Python to include the current directory in its search path, allowing the scripts to import modules from the main app