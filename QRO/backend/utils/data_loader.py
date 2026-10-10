"""
Data loading utilities for QuantumRoute.
"""

import json
import os


def load_json(file_path):
    """
    Load JSON data from a file.

    Parameters
    ----------
    file_path : str
        Path to JSON file.

    Returns
    -------
    dict or list
        JSON data.
    """

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_json(
    file_path,
    data
):
    """
    Save Python data as JSON.
    """

    directory = os.path.dirname(
        file_path
    )

    if directory:

        os.makedirs(
            directory,
            exist_ok=True
        )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )

    return True