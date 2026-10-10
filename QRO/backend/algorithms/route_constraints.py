"""
Route constraint utilities for QuantumRoute.

The project uses a simple 2D coordinate system for locations.

Example location:
{
    "id": "A",
    "x": 10,
    "y": 20
}

Example delivery:
{
    "id": "D1",
    "location_id": "A",
    "demand": 10,
    "earliest": 0,
    "latest": 100
}
"""

from math import sqrt


def calculate_distance(location_a, location_b):
    """
    Calculate Euclidean distance between two locations.
    """

    dx = location_a["x"] - location_b["x"]
    dy = location_a["y"] - location_b["y"]

    return sqrt(dx * dx + dy * dy)


def calculate_route_distance(route, locations):
    """
    Calculate total distance of a route.

    route example:
    ["DEPOT", "A", "B", "C", "DEPOT"]
    """

    location_map = {
        location["id"]: location
        for location in locations
    }

    total_distance = 0.0

    for i in range(len(route) - 1):
        current = location_map[route[i]]
        next_location = location_map[route[i + 1]]

        total_distance += calculate_distance(
            current,
            next_location
        )

    return round(total_distance, 2)


def check_capacity(route, deliveries, vehicle_capacity):
    """
    Check whether total delivery demand fits
    inside the vehicle capacity.
    """

    delivery_map = {
        delivery["location_id"]: delivery
        for delivery in deliveries
    }

    total_demand = 0

    for location_id in route:
        if location_id in delivery_map:
            total_demand += delivery_map[location_id]["demand"]

    return total_demand <= vehicle_capacity


def calculate_total_demand(route, deliveries):
    """
    Calculate total demand on a route.
    """

    delivery_map = {
        delivery["location_id"]: delivery
        for delivery in deliveries
    }

    total_demand = 0

    for location_id in route:
        if location_id in delivery_map:
            total_demand += delivery_map[location_id]["demand"]

    return total_demand


def check_time_windows(
    route,
    locations,
    deliveries,
    average_speed=1.0
):
    """
    Check whether the vehicle can reach every delivery
    within its time window.

    average_speed:
        Distance units per time unit.
    """

    location_map = {
        location["id"]: location
        for location in locations
    }

    delivery_map = {
        delivery["location_id"]: delivery
        for delivery in deliveries
    }

    current_time = 0.0

    for i in range(len(route) - 1):

        current_location = location_map[route[i]]
        next_location = location_map[route[i + 1]]

        distance = calculate_distance(
            current_location,
            next_location
        )

        travel_time = distance / average_speed

        current_time += travel_time

        if route[i + 1] in delivery_map:

            delivery = delivery_map[route[i + 1]]

            earliest = delivery.get("earliest", 0)
            latest = delivery.get("latest", float("inf"))

            # Wait if vehicle arrives early
            if current_time < earliest:
                current_time = earliest

            # Reject if vehicle arrives too late
            if current_time > latest:
                return False

    return True


def validate_route(
    route,
    locations,
    deliveries,
    vehicle_capacity,
    average_speed=1.0
):
    """
    Validate a complete route.
    """

    capacity_ok = check_capacity(
        route,
        deliveries,
        vehicle_capacity
    )

    time_ok = check_time_windows(
        route,
        locations,
        deliveries,
        average_speed
    )

    return {
        "valid": capacity_ok and time_ok,
        "capacity_ok": capacity_ok,
        "time_window_ok": time_ok
    }


def calculate_route_cost(
    route_distance,
    fuel_cost_per_distance=10.0,
    time_cost_per_unit=2.0
):
    """
    Calculate a simple operational cost.
    """

    estimated_time = route_distance

    fuel_cost = (
        route_distance *
        fuel_cost_per_distance
    )

    time_cost = (
        estimated_time *
        time_cost_per_unit
    )

    total_cost = fuel_cost + time_cost

    return round(total_cost, 2)