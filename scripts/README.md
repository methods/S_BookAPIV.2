# MongoDB Data Management Scripts

## Overview

This directory contains two command-line scripts for managing the 'books' collection in a MongoDB database. These tools are designed to help developers quickly set up a uniform, clean environment for testing and development.

-   **`delete_books.py`**: A script to perform a hard delete of all documents from the books collection.
-   **`create_books.py`**: A script that reads a local JSON file and populates the database, ensuring data uniformity by replacing existing books or inserting new ones (an "upsert" operation).

---

## Prerequisites

Before running these scripts, please ensure you have the following set up:

1.  **Python 3.x** installed.
2.  **A running MongoDB instance.** The scripts are configured to connect to `mongodb://localhost:27017/` by default.
3.  **Required Python packages installed.** You can install them from the root directory of the repository with:
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

The easiest way to run the scripts is by using the `Makefile` from the root of the project.

### Using Make Targets

| Command | Description |
| :--- | :--- |
| `make clean` | Runs the `delete_books.py` script to clear the collection. |
| `make books` | Runs the `create_books.py` script to populate the collection. |
| `make setup` | A convenient target that runs `make clean` and then `make books` for a full database reset. |

### Running Scripts Directly

You can also run the Python scripts directly from your terminal.

**To delete all books:**

```bash
python scripts/delete_books.py