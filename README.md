# S_BookAPIV.2

## Project Overview

This project provides a books API that will allow users to add, retrieve, reserve and edit books on a database. 

- [Contributing Guidelines](CONTRIBUTING.md)
- [License Information](LICENSE.md)

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3**: Version 3.7 or newer is recommended. You can download it from [python.org](https://www.python.org/downloads/).
*   **pip**: Python's package installer. It usually comes with Python installations.
*   **make**: A build automation tool. Pre-installed on macOS/Linux. Windows users may need to install it (e.g., via Chocolatey or WSL).
* [Docker](https://formulae.brew.sh/formula/docker)
* [Colima](https://github.com/abiosoft/colima) (for Mac/Linux users)
* [mongosh](https://www.mongodb.com/try/download/shell) (MongoDB shell client)
* *(Optional)* [MongoDB Compass](https://www.mongodb.com/try/download/compass) (GUI client)

## Getting Started: A Step-by-Step Guide

### Step 1: Clone the Repository
This project uses a `Makefile` to automate setup and common tasks.

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:methods/S_BookAPIV.2.git
    cd S_BookAPIV.2
    ```

2.  **View available commands:**
    To see a list of all available commands, run:
    ```bash
    make help
    ```

### Step 2: Set Up and Run MongoDB

This project requires MongoDB to be running locally. We recommend using **Docker** and **Colima** for a lightweight, consistent environment.

#### 1: Start Colima

```bash
colima start
```

#### 2: Run the MongoDB Container: (This will pull the image if it's not already local)

```bash
docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest
```

#### 3: Verify MongoDB is Running

```
docker ps
docker ps -a
```

Look for a container named mongodb with port 27017 exposed. You can also connect via mongosh or MongoDB Compass to confirm.



### Step 3: Install Project Dependencies

The `Makefile` will create a local virtual environment (venv) and install all required Python packages. You only need to run this once.

```bash
make install
```

### Step 4: Set Up the Database

To perform a full database reset and populate it with initial data for development, run the main setup command:
```bash
make setup
```
This single command will clean the database and then populate it with books, users, and reservations, ensuring a consistent state for all developers.

For more granular control, you can use the individual commands below. For more details on what each script does, see [Scripts Documentation](scripts/README.md)

To use the API, you first need to populate the database with some initial data.

| Command | Description |
|---------------------|-----------------------------------------------------------------------------|
| make setup | (Recommended) Resets the entire database and seeds all data. |
| make clean-db | Deletes ALL books and reservations. Useful for starting fresh. |
| make books | Populates the database with books from scripts/test_data/books.json. |
| make reservations | Populates the database with reservations from scripts/test_data/reservations.json. |
| make seed-users | Populates the database with users from scripts/test_data/sample_user_data.json. |



### Step 5: Run the API

With the database seeded, you can now run the Flask application.

```bash
make run
```
The API will be available at http://127.0.0.1:5000.

--- 

## Development Tasks

Here are other common commands for development, testing, and maintenance.

### Testing and Coverage

This project uses pytest to run tests and coverage.py to measure code coverage.
To run the test suite and see the coverage report:

```bash
make test
```

If old data is persisting, you can use an explicit
```bash
coverage erase
```
command to clean out the old data.


### Code Quality (Linting)

This project uses Pylint to check code quality and style.

To run the linter

```bash
make lint
```


### Clean the Project

To remove the virtual environment and all Python cache files (__pycache__, .coverage, etc.):

```bash
make clean
```
This is useful if you want to start with a fresh environment.


## License
This project is licensed under the MIT License - see the LICENSE.md file for details.