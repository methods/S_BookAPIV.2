""" Collection of helper fucntions """

from urllib.parse import urljoin

def append_hostname(book, host):
    """Helper function to append the hostname to the links in a book object."""
    if "links" in book:
        book["links"] = {
            key: urljoin(host, path)
            for key, path in book["links"].items()
        }
    return book
