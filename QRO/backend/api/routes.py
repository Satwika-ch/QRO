
"""
REST API routes for QuantumRoute.
Dynamic location + delivery routing.
"""

from flask import request, jsonify
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import math

from . import api
from .optimization import (
    run_optimization,
    run_multi_vehicle_optimization,
)
from algorithms.classical_optimizer import optimize_classical


# ============================================================
# GEOCODING
# ============================================================

def build_address(data):
    """Build a searchable address from country/state/city/address."""
    parts = [
        data.get("address"),
        data.get("city"),
        data.get("state"),
        data.get("country"),
    ]

    return ", ".join(
        str(part).strip()
        for part in parts
        if part and str(part).strip()
    )


def geocode_address(address):
    """
    Convert a human-readable location into latitude/longitude
    using OpenStreetMap Nominatim.
    """
    if not address or not str(address).strip():
        raise ValueError("Location address is empty.")

    url = (
        "https://nominatim.openstreetmap.org/search"
        "?format=json"
        "&limit=1"
        "&q=" + quote(str(address).strip())
    )

    request_obj = Request(
        url,
        headers={"User-Agent": "QuantumRoute/1.0"},
    )

    with urlopen(request_obj, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result:
        raise ValueError(f"Location not found: {address}")

    return {
        "latitude": float(result[0]["lat"]),
        "longitude": float(result[0]["lon"]),
        "display_name": result[0].get("display_name", address),
    }


# ============================================================
# COORDINATE CONVERSION
# ============================================================

def latlon_to_xy(latitude, longitude, depot_lat, depot_lon):
    """
    Convert geographic coordinates to local X/Y coordinates.
    These X/Y values are used by the existing optimizer.
    """
    earth_radius_km = 6371.0

    lat1 = math.radians(depot_lat)
    lat2 = math.radians(latitude)

    delta_lat = math.radians(latitude - depot_lat)
    delta_lon = math.radians(longitude - depot_lon)

    x = (
        earth_radius_km
        * delta_lon
        * math.cos((lat1 + lat2) / 2)
    )

    y = earth_radius_km * delta_lat

    return x, y


# ============================================================
# HEALTH
# ============================================================

@api.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "QuantumRoute backend is running",
    })


# ============================================================
# VEHICLES
# ============================================================

@api.route("/vehicles", methods=["GET"])
def get_vehicles():
    """Return the five registered demo vehicles."""

    vehicles = [
        {
            "id": "V1",
            "name": "Vehicle 1",
            "capacity": 50,
            "available": True,
            "status": "active",
            "latitude": None,
            "longitude": None,
            "route": [],
        },
        {
            "id": "V2",
            "name": "Vehicle 2",
            "capacity": 75,
            "available": True,
            "status": "active",
            "latitude": None,
            "longitude": None,
            "route": [],
        },
        {
            "id": "V3",
            "name": "Vehicle 3",
            "capacity": 60,
            "available": True,
            "status": "active",
            "latitude": None,
            "longitude": None,
            "route": [],
        },
        {
            "id": "V4",
            "name": "Vehicle 4",
            "capacity": 80,
            "available": True,
            "status": "active",
            "latitude": None,
            "longitude": None,
            "route": [],
        },
        {
            "id": "V5",
            "name": "Vehicle 5",
            "capacity": 70,
            "available": True,
            "status": "active",
            "latitude": None,
            "longitude": None,
            "route": [],
        },
    ]

    return jsonify({
        "success": True,
        "total_vehicles": len(vehicles),
        "active_vehicles": sum(
            1 for vehicle in vehicles
            if vehicle["status"] == "active"
        ),
        "available_vehicles": sum(
            1 for vehicle in vehicles
            if vehicle["available"]
        ),
        "vehicles": vehicles,
    })


# ============================================================
# LOCATIONS
# ============================================================

@api.route("/locations", methods=["GET"])
def get_locations():
    return jsonify({
        "success": True,
        "locations": [],
    })


# ============================================================
# GEOCODE
# ============================================================

@api.route("/geocode", methods=["POST"])
def geocode():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is empty.",
            }), 400

        address = build_address(data)

        if not address:
            return jsonify({
                "success": False,
                "error": "Location details are required.",
            }), 400

        result = geocode_address(address)

        return jsonify({
            "success": True,
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "display_name": result["display_name"],
        })

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500


# ============================================================
# BUILD DYNAMIC LOCATIONS
# ============================================================

def build_dynamic_locations(data):
    depot = data.get("depot")
    deliveries = data.get("deliveries")

    if not isinstance(depot, dict) or not depot:
        raise ValueError("Depot information is required.")

    if not isinstance(deliveries, list) or not deliveries:
        raise ValueError("At least one delivery is required.")

    # Geocode depot.
    depot_address = build_address(depot)

    if not depot_address:
        raise ValueError("Depot address details are required.")

    depot_geo = geocode_address(depot_address)

    depot_lat = depot_geo["latitude"]
    depot_lon = depot_geo["longitude"]

    locations = [
        {
            "id": "DEPOT",
            "x": 0.0,
            "y": 0.0,
            "latitude": depot_lat,
            "longitude": depot_lon,
            "display_name": depot_geo["display_name"],
        }
    ]

    processed_deliveries = []
    used_location_ids = {"DEPOT"}
    used_delivery_ids = set()

    # Geocode delivery locations.
    for index, delivery in enumerate(deliveries, start=1):
        if not isinstance(delivery, dict):
            raise ValueError(
                f"Delivery {index} must be an object."
            )

        delivery_id = str(
            delivery.get("id") or f"D{index:03d}"
        )

        if delivery_id in used_delivery_ids:
            raise ValueError(
                f"Duplicate delivery ID: {delivery_id}"
            )

        used_delivery_ids.add(delivery_id)

        address = build_address(delivery)

        if not address:
            raise ValueError(
                f"Location information missing for delivery "
                f"{delivery_id}."
            )

        demand = float(delivery.get("demand", 0))

        if not math.isfinite(demand) or demand < 0:
            raise ValueError(
                f"Demand for delivery {delivery_id} "
                "must be a non-negative number."
            )

        geo = geocode_address(address)

        x, y = latlon_to_xy(
            geo["latitude"],
            geo["longitude"],
            depot_lat,
            depot_lon,
        )

        location_id = str(
            delivery.get("location_id") or delivery_id
        )

        if location_id in used_location_ids:
            raise ValueError(
                f"Duplicate location ID: {location_id}"
            )

        used_location_ids.add(location_id)

        locations.append({
            "id": location_id,
            "x": x,
            "y": y,
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "display_name": geo["display_name"],
        })

        processed_deliveries.append({
            "id": delivery_id,
            "location_id": location_id,
            "demand": demand,
            "country": delivery.get("country"),
            "state": delivery.get("state"),
            "city": delivery.get("city"),
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
        })

    return locations, processed_deliveries, depot_geo


# ============================================================
# MULTI-VEHICLE OPTIMIZATION
# Does not replace the existing Quantum/Classical endpoint.
# ============================================================

@api.route("/multi-vehicle-optimize", methods=["POST"])
def multi_vehicle_optimize():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is empty.",
            }), 400

        locations, deliveries, depot_geo = (
            build_dynamic_locations(data)
        )

        # Preserve existing demo fleet capacities.
        vehicles = [
            {
                "id": "V1",
                "name": "Vehicle 1",
                "capacity": 50,
                "available": True,
                "status": "active",
            },
            {
                "id": "V2",
                "name": "Vehicle 2",
                "capacity": 75,
                "available": True,
                "status": "active",
            },
            {
                "id": "V3",
                "name": "Vehicle 3",
                "capacity": 60,
                "available": True,
                "status": "active",
            },
            {
                "id": "V4",
                "name": "Vehicle 4",
                "capacity": 80,
                "available": True,
                "status": "active",
            },
            {
                "id": "V5",
                "name": "Vehicle 5",
                "capacity": 70,
                "available": True,
                "status": "active",
            },
        ]

        result = run_multi_vehicle_optimization(
            locations=locations,
            deliveries=deliveries,
            vehicles=vehicles,
            depot_id="DEPOT",
        )

        result["depot"] = depot_geo
        result["locations"] = locations
        result["deliveries"] = deliveries

        return jsonify(result), (
            200 if result.get("success") else 400
        )

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500


# ============================================================
# EXISTING QUANTUM + CLASSICAL OPTIMIZATION
# Preserved for compatibility.
# ============================================================

@api.route("/optimize", methods=["POST"])
def optimize_route():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is empty.",
            }), 400

        # NEW DYNAMIC FORMAT.
        if data.get("depot") and data.get("deliveries"):
            locations, deliveries, depot_geo = (
                build_dynamic_locations(data)
            )

            vehicle_capacity = data.get("vehicle_capacity")

            if vehicle_capacity is None:
                return jsonify({
                    "success": False,
                    "error": "Vehicle capacity is required.",
                }), 400

            vehicle_capacity = float(vehicle_capacity)

            if (
                not math.isfinite(vehicle_capacity)
                or vehicle_capacity <= 0
            ):
                return jsonify({
                    "success": False,
                    "error": (
                        "Vehicle capacity must be a "
                        "positive number."
                    ),
                }), 400

            total_demand = sum(
                delivery["demand"]
                for delivery in deliveries
            )

            if total_demand > vehicle_capacity:
                return jsonify({
                    "success": False,
                    "error": (
                        "Total delivery demand exceeds "
                        "vehicle capacity."
                    ),
                    "total_demand": total_demand,
                    "vehicle_capacity": vehicle_capacity,
                }), 400

            result = run_optimization(
                locations=locations,
                deliveries=deliveries,
                vehicle_capacity=vehicle_capacity,
                depot_id="DEPOT",
            )

            # Preserve geographic information in the response.
            result["depot"] = depot_geo
            result["locations"] = locations
            result["deliveries"] = deliveries

            return jsonify(result), (
                200 if result.get("success") else 400
            )

        # OLD FORMAT — kept for compatibility.
        locations = data.get("locations")
        deliveries = data.get("deliveries")
        vehicle_capacity = data.get("vehicle_capacity")
        depot_id = data.get("depot_id", "DEPOT")

        if not locations:
            return jsonify({
                "success": False,
                "error": "Locations are required.",
            }), 400

        if not deliveries:
            return jsonify({
                "success": False,
                "error": "Deliveries are required.",
            }), 400

        if vehicle_capacity is None:
            return jsonify({
                "success": False,
                "error": "Vehicle capacity is required.",
            }), 400

        vehicle_capacity = float(vehicle_capacity)

        if (
            not math.isfinite(vehicle_capacity)
            or vehicle_capacity <= 0
        ):
            return jsonify({
                "success": False,
                "error": (
                    "Vehicle capacity must be a positive number."
                ),
            }), 400

        result = run_optimization(
            locations=locations,
            deliveries=deliveries,
            vehicle_capacity=vehicle_capacity,
            depot_id=depot_id,
        )

        return jsonify(result), (
            200 if result.get("success") else 400
        )

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500


# ============================================================
# EXISTING CLASSICAL OPTIMIZATION
# Preserved for compatibility.
# ============================================================

@api.route("/classical-optimize", methods=["POST"])
def classical_optimize():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is empty.",
            }), 400

        locations = data.get("locations")
        deliveries = data.get("deliveries")
        vehicle_capacity = data.get("vehicle_capacity")
        depot_id = data.get("depot_id", "DEPOT")

        if not locations:
            return jsonify({
                "success": False,
                "error": "Locations are required.",
            }), 400

        if not deliveries:
            return jsonify({
                "success": False,
                "error": "Deliveries are required.",
            }), 400

        if vehicle_capacity is None:
            return jsonify({
                "success": False,
                "error": "Vehicle capacity is required.",
            }), 400

        vehicle_capacity = float(vehicle_capacity)

        if (
            not math.isfinite(vehicle_capacity)
            or vehicle_capacity <= 0
        ):
            return jsonify({
                "success": False,
                "error": (
                    "Vehicle capacity must be a positive number."
                ),
            }), 400

        result = optimize_classical(
            locations=locations,
            deliveries=deliveries,
            vehicle_capacity=vehicle_capacity,
            depot_id=depot_id,
        )

        return jsonify(result), (
            200 if result.get("success") else 400
        )

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500

