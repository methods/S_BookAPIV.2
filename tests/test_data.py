"""Constants which couldnt be added to conftest"""


# A dictionary for headers to keep things clean
HEADERS = {
    "VALID": {"X-API-KEY": "test-key-123"},
    "INVALID": {"X-API-KEY": "This-is-the-wrong-key-12345"},
    "MISSING": {},
}

# A sample payload for POST/PUT requests
DUMMY_PAYLOAD = {
    "title": "A Test Book",
    "synopsis": "A test synopsis.",
    "author": "Tester McTestFace",
}
