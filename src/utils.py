import os
import json

import requests


def find_file(name, path):
    """
    Finds file with the specified name in the given path.

    Args:
        name (str): file name.
        path (str): starting path for search.

    Returns:
        str: absolute file path (if found)
    """
    for root, dirs, files in os.walk(path, followlinks=True):
        for file in files:
            if name in file:
                return os.path.join(root, file)


def read(path):
    """
    Reads and returns the content of given file.

    Args:
        path (str): file path.

    Returns:
        str: file content.
    """
    with open(path) as f:
        return f.read()


def write_json(path, content):
    """
    Writes a given JSON content.

    Args:
        path (str): file path.
        content (dict): content.
    """
    with open(path, "w+") as f:
        f.write(json.dumps(content, indent=4))


def read_json(path):
    """
    Reads and returns the content of given file in JSON format.

    Args:
        path (str): file path.

    Returns:
        dict: file content.
    """
    return json.loads(read(path))


def upload_file(file_):
    """
    Uploads a given file.

    Args:
        file_ (dict): a dictionary with path and presignedURL keys.
    """
    path = file_["path"]
    session = requests.Session()
    headers = {"Content-Length": str(os.path.getsize(path))}
    with open(path) as f:
        session.request("PUT", file_["URL"], data=f, headers=headers).raise_for_status()