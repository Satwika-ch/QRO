"""
Route service for QuantumRoute.
"""

import json
import os

from algorithms.route_constraints import (
    calculate_route_distance,
    calculate_total_demand,
    validate_route,
    calculate_route_cost
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


def load_json(filename):
    """
    Load a JSON file from the data folder.
    """

    file_path = os.path.join(
        DATA_DIR,
        filename
    )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def get_locations():
    """
    Return all locations.
    """

    return load_json(
        "locations.json"
    )


def get_deliveries():
    """
    Return all deliveries.
    """

    return load_json(
        "deliveries.json"
    )


def calculate_route_details(
    route,
    vehicle_capacity
):
    """
    Calculate complete information
    about a route.
    """

    locations = get_locations()
    deliveries = get_deliveries()

    distance = calculate_route_distance(
        route,
        locations
    )

    demand = calculate_total_demand(
        route,
        deliveries
    )

    validation = validate_route(
        route=route,
        locations=locations,
        deliveries=deliveries,
        vehicle_capacity=vehicle_capacity
    )

    cost = calculate_route_cost(
        distance
    )

    return {
        "route": route,
        "distance": distance,
        "demand": demand,
        "cost": cost,
        "valid": validation["valid"],
        "capacity_ok": validation["capacity_ok"],
        "time_window_ok": validation["time_window_ok"]
    }