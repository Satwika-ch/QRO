"""
Distance utility functions for QuantumRoute.
"""

import math


def euclidean_distance(point1, point2):
    """
    Calculate the Euclidean distance between two points.

    Parameters
    ----------
    point1 : tuple
        (x, y) coordinates.

    point2 : tuple
        (x, y) coordinates.

    Returns
    -------
    float
        Distance between the two points.
    """

    x1, y1 = point1
    x2, y2 = point2

    distance = math.sqrt(
        (x2 - x1) ** 2
        +
        (y2 - y1) ** 2
    )

    return round(distance, 2)


def location_distance(location1, location2):
    """
    Calculate distance between two location dictionaries.
    """

    point1 = (
        float(location1["x"]),
        float(location1["y"])
    )

    point2 = (
        float(location2["x"]),
        float(location2["y"])
    )

    return euclidean_distance(
        point1,
        point2
    )


def calculate_total_distance(
    route,
    locations
):
    """
    Calculate total distance of a route.

    Example:

        DEPOT -> A -> B -> C -> DEPOT
    """

    location_map = {
        location["id"]: location
        for location in locations
    }

    total_distance = 0.0

    for i in range(
        len(route) - 1
    ):

        current_id = route[i]
        next_id = route[i + 1]

        if (
            current_id not in location_map
            or
            next_id not in location_map
        ):
            raise ValueError(
                "Invalid location in route."
            )

        distance = location_distance(
            location_map[current_id],
            location_map[next_id]
        )

        total_distance += distance

    return round(
        total_distance,
        2
    )