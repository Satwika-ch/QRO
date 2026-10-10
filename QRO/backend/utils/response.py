"""
API response utilities for QuantumRoute.
"""


def success_response(
    data=None,
    message="Success"
):
    """
    Create a successful response.
    """

    response = {
        "success": True,
        "message": message
    }

    if data is not None:

        response["data"] = data

    return response


def error_response(
    message,
    error_code=None
):
    """
    Create an error response.
    """

    response = {
        "success": False,
        "message": message
    }

    if error_code is not None:

        response["error_code"] = error_code

    return response