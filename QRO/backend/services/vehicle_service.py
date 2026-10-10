"""
Vehicle service for QuantumRoute.
"""

from .route_service import load_json


def get_vehicles():
    """
    Return all vehicles.
    """

    return load_json(
        "vehicles.json"
    )


def get_vehicle_by_id(vehicle_id):
    """
    Find a vehicle using its ID.
    """

    vehicles = get_vehicles()

    for vehicle in vehicles:

        if vehicle["id"] == vehicle_id:

            return vehicle

    return None


def get_available_vehicles():
    """
    Return only available vehicles.
    """

    vehicles = get_vehicles()

    return [
        vehicle
        for vehicle in vehicles
        if vehicle.get(
            "available",
            False
        )
    ]


def check_vehicle_capacity(
    vehicle_id,
    total_demand
):
    """
    Check whether a particular vehicle
    can handle the delivery demand.
    """

    vehicle = get_vehicle_by_id(
        vehicle_id
    )

    if vehicle is None:

        return {
            "success": False,
            "message": "Vehicle not found."
        }

    capacity = vehicle["capacity"]

    return {
        "success": True,
        "vehicle_id": vehicle_id,
        "capacity": capacity,
        "demand": total_demand,
        "can_carry": (
            total_demand <= capacity
        )
    }