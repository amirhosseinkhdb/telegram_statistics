import json
from pathlib import Path
from typing import Union


def read_json(file_path: Union[str, Path]) -> dict:
    """Reads a json file and returns the dict

    :param file_path: path to json file directory
    :return: dictionary of json file
    """
    with open(file_path) as f:
        return json.load(f)


def read_file(file_path: Union[str, Path]) -> str:
    """Reads a file and returns the content

    :param file_path: path to file directory
    :return: content of the file
    """
    with open(file_path) as f:
        return f.read()
