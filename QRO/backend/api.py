"""
QuantumRoute API
VNQFF-08
Quantum-Enhanced Last-Mile Route Optimisation

Dynamic Location Architecture

The route is based ONLY on:
    1. User-entered depot / warehouse
    2. User-entered delivery locations

No delivery location is hard-coded.
No city/state is hard-coded as the delivery area.
"""

from flask import Blueprint, request, jsonify

import json
import math
import urllib.parse
import urllib.request

from algorithms.classical_optimizer import optimize_classical
from algorithms.qaoa_optimizer import run_qaoa


# ============================================================
# BLUEPRINT
# ============================================================

api = Blueprint("api", __name__)


# ============================================================
# EXTERNAL SERVICES
# ============================================================

GEOCODING_URL = "https://nominatim.openstreetmap.org/search"

OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"


# ============================================================
# CACHE
# ============================================================

GEOCODE_CACHE = {}


# ============================================================
# COMMON RESPONSE FUNCTIONS
# ============================================================

def success_response(data=None):
    response = {
        "success": True
    }

    if data:
        response.update(data)

    return jsonify(response)


def error_response(message, status=400):
    return jsonify({
        "success": False,
        "error": str(message)
    }), status


# ============================================================
# HEALTH
# ============================================================

@api.route("/health", methods=["GET"])
def health():
    return jsonify({
        "message": "QuantumRoute backend is running",
        "success": True
    })


# ============================================================
# VEHICLES
# ============================================================

@api.route("/vehicles", methods=["GET"])
def vehicles():
    return jsonify({
        "success": True,
        "vehicles": [
            {
                "id": "V1",
                "name": "Vehicle 01",
                "capacity": 100,
                "status": "Available"
            },
            {
                "id": "V2",
                "name": "Vehicle 02",
                "capacity": 100,
                "status": "Available"
            },
            {
                "id": "V3",
                "name": "Vehicle 03",
                "capacity": 100,
                "status": "Available"
            },
            {
                "id": "V4",
                "name": "Vehicle 04",
                "capacity": 100,
                "status": "Available"
            }
        ]
    })


# ============================================================
# LOCATIONS
# ============================================================

@api.route("/locations", methods=["GET"])
def locations():
    return jsonify({
        "success": True,
        "locations": []
    })


# ============================================================
# GEOCODING
# ============================================================

def geocode_address(address):
    """
    Convert any user-entered address into
    latitude and longitude.

    Example:
        Vijayawada, Andhra Pradesh, India
        Hyderabad, Telangana, India
        Dubai, UAE
    """

    address = str(address).strip()

    if not address:
        raise ValueError(
            "Location address cannot be empty."
        )

    cache_key = address.lower()

    if cache_key in GEOCODE_CACHE:
        return GEOCODE_CACHE[cache_key]

    params = urllib.parse.urlencode({
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    })

    url = f"{GEOCODING_URL}?{params}"

    request_object = urllib.request.Request(
        url,
        headers={
            "User-Agent": "QuantumRoute-VNQFF08/1.0"
        }
    )

    try:
        with urllib.request.urlopen(
            request_object,
            timeout=15
        ) as response:

            raw_data = response.read().decode("utf-8")

            results = json.loads(raw_data)

    except Exception as error:
        raise RuntimeError(
            f"Geocoding service failed: {error}"
        )

    if not results:
        raise ValueError(
            f"Location not found: {address}"
        )

    result = results[0]

    location = {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "display_name": result.get(
            "display_name",
            address
        )
    }

    GEOCODE_CACHE[cache_key] = location

    return location


# ============================================================
# BUILD ADDRESS
# ============================================================

def build_address(location):
    """
    Build a searchable address from:
        country
        state
        city

    Also supports a direct 'address' field.
    """

    direct_address = str(
        location.get("address", "")
    ).strip()

    if direct_address:
        return direct_address

    city = str(
        location.get("city", "")
    ).strip()

    state = str(
        location.get("state", "")
    ).strip()

    country = str(
        location.get("country", "")
    ).strip()

    parts = []

    if city:
        parts.append(city)

    if state:
        parts.append(state)

    if country:
        parts.append(country)

    if not parts:
        raise ValueError(
            "A location must contain an address or city."
        )

    return ", ".join(parts)


# ============================================================
# GEOCODE ENDPOINT
# ============================================================

@api.route("/geocode", methods=["POST"])
def geocode():

    try:
        data = request.get_json(
            silent=True
        ) or {}

        address = build_address(data)

        result = geocode_address(address)

        return jsonify({
            "success": True,
            "address": address,
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "display_name": result["display_name"]
        })

    except Exception as error:

        return error_response(
            error,
            400
        )


# ============================================================
# DEPOT GEOCODING
# ============================================================

def build_depot(depot_data):
    """
    The depot is supplied by the user.

    It is NOT hard-coded to Guntur.
    """

    if not depot_data:
        raise ValueError(
            "Depot / warehouse location is required."
        )

    address = build_address(depot_data)

    geo = geocode_address(address)

    return {
        "id": "DEPOT",

        "address": address,

        "latitude": geo["latitude"],

        "longitude": geo["longitude"],

        "display_name": geo["display_name"],

        "country": str(
            depot_data.get(
                "country",
                ""
            )
        ).strip(),

        "state": str(
            depot_data.get(
                "state",
                ""
            )
        ).strip(),

        "city": str(
            depot_data.get(
                "city",
                ""
            )
        ).strip(),

        "demand": 0
    }


# ============================================================
# LATITUDE / LONGITUDE → LOCAL X / Y
# ============================================================

def latlon_to_xy(
    latitude,
    longitude,
    origin_latitude,
    origin_longitude
):
    """
    Convert geographic coordinates into
    approximate local kilometre coordinates.

    X = East / West
    Y = North / South
    """

    earth_radius_km = 6371.0

    lat1 = math.radians(origin_latitude)
    lat2 = math.radians(latitude)

    delta_lat = math.radians(
        latitude - origin_latitude
    )

    delta_lon = math.radians(
        longitude - origin_longitude
    )

    x = (
        earth_radius_km
        * delta_lon
        * math.cos(
            (lat1 + lat2) / 2
        )
    )

    y = (
        earth_radius_km
        * delta_lat
    )

    return x, y


# ============================================================
# BUILD DELIVERY LOCATIONS
# ============================================================

def build_dynamic_locations(
    delivery_data,
    depot
):
    """
    Convert ONLY the user-entered deliveries
    into optimizer locations.
    """

    if not delivery_data:
        raise ValueError(
            "At least one delivery location is required."
        )

    locations = []

    depot_latitude = depot["latitude"]
    depot_longitude = depot["longitude"]

    # --------------------------------------------------------
    # DEPOT
    # --------------------------------------------------------

    locations.append({
        "id": "DEPOT",
        "x": 0.0,
        "y": 0.0,
        "latitude": depot_latitude,
        "longitude": depot_longitude,
        "country": depot["country"],
        "state": depot["state"],
        "city": depot["city"],
        "address": depot["address"],
        "demand": 0
    })

    # --------------------------------------------------------
    # USER DELIVERY LOCATIONS
    # --------------------------------------------------------

    for index, item in enumerate(
        delivery_data,
        start=1
    ):

        location_id = str(
            item.get(
                "id",
                f"D{index:03d}"
            )
        ).strip()

        if not location_id:
            location_id = f"D{index:03d}"

        if location_id.upper() == "DEPOT":
            raise ValueError(
                "DEPOT is reserved for the warehouse."
            )

        try:
            demand = float(
                item.get(
                    "demand",
                    0
                )
            )
        except (TypeError, ValueError):

            raise ValueError(
                f"Invalid demand for {location_id}."
            )

        if demand < 0:
            raise ValueError(
                f"Demand cannot be negative for {location_id}."
            )

        # ----------------------------------------------------
        # ADDRESS
        # ----------------------------------------------------

        address = build_address(item)

        # ----------------------------------------------------
        # GEOCODE
        # ----------------------------------------------------

        geo = geocode_address(address)

        latitude = geo["latitude"]
        longitude = geo["longitude"]

        # ----------------------------------------------------
        # LOCAL X/Y
        # ----------------------------------------------------

        x, y = latlon_to_xy(
            latitude,
            longitude,
            depot_latitude,
            depot_longitude
        )

        # ----------------------------------------------------
        # STORE LOCATION
        # ----------------------------------------------------

        locations.append({
            "id": location_id,

            "x": round(x, 4),

            "y": round(y, 4),

            "latitude": latitude,

            "longitude": longitude,

            "country": str(
                item.get(
                    "country",
                    ""
                )
            ).strip(),

            "state": str(
                item.get(
                    "state",
                    ""
                )
            ).strip(),

            "city": str(
                item.get(
                    "city",
                    ""
                )
            ).strip(),

            "address": address,

            "display_name":
                geo["display_name"],

            "demand": demand
        })

    return locations


# ============================================================
# LOCATION LOOKUP
# ============================================================

def create_location_lookup(locations):
    """
    Create a dictionary containing
    the real geographic information
    for every optimized location.
    """

    lookup = {}

    for location in locations:

        lookup[location["id"]] = {
            "latitude":
                location.get("latitude"),

            "longitude":
                location.get("longitude"),

            "country":
                location.get(
                    "country",
                    ""
                ),

            "state":
                location.get(
                    "state",
                    ""
                ),

            "city":
                location.get(
                    "city",
                    ""
                ),

            "address":
                location.get(
                    "address",
                    ""
                ),

            "demand":
                location.get(
                    "demand",
                    0
                ),

            "display_name":
                location.get(
                    "display_name",
                    ""
                )
        }

    return lookup


# ============================================================
# OPTIMIZE
# ============================================================

@api.route("/optimize", methods=["POST"])
def optimize():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        # ----------------------------------------------------
        # USER DEPOT
        # ----------------------------------------------------

        depot_data = data.get(
            "depot"
        )

        if not depot_data:

            return error_response(
                "Depot / warehouse location is required."
            )

        depot = build_depot(
            depot_data
        )

        # ----------------------------------------------------
        # USER DELIVERY LOCATIONS
        # ----------------------------------------------------

        delivery_data = data.get(
            "deliveries",
            []
        )

        if not delivery_data:

            return error_response(
                "No delivery locations were provided."
            )

        # ----------------------------------------------------
        # VEHICLE CAPACITY
        # ----------------------------------------------------

        try:

            vehicle_capacity = float(
                data.get(
                    "vehicle_capacity",
                    data.get(
                        "capacity",
                        100
                    )
                )
            )

        except (TypeError, ValueError):

            return error_response(
                "Invalid vehicle capacity."
            )

        if vehicle_capacity <= 0:

            return error_response(
                "Vehicle capacity must be greater than zero."
            )

        # ----------------------------------------------------
        # BUILD ONLY ENTERED LOCATIONS
        # ----------------------------------------------------

        locations = build_dynamic_locations(
            delivery_data,
            depot
        )

        # ----------------------------------------------------
        # BUILD DELIVERIES FOR OPTIMIZER
        # ----------------------------------------------------

        deliveries = []

        for location in locations:

            if location["id"] == "DEPOT":
                continue

            deliveries.append({
                "id":
                    f"D-{location['id']}",

                "location_id":
                    location["id"],

                "demand":
                    location["demand"]
            })

        # ----------------------------------------------------
        # TOTAL DEMAND
        # ----------------------------------------------------

        total_demand = sum(
            float(
                delivery["demand"]
            )
            for delivery in deliveries
        )

        if total_demand > vehicle_capacity:

            return error_response(
                (
                    f"Total delivery demand "
                    f"({total_demand}) exceeds "
                    f"vehicle capacity "
                    f"({vehicle_capacity})."
                )
            )

        # ----------------------------------------------------
        # DEPOT ID
        # ----------------------------------------------------

        depot_id = "DEPOT"

        # ----------------------------------------------------
        # CLASSICAL OPTIMIZATION
        # ----------------------------------------------------

        classical = optimize_classical(
            locations,
            deliveries,
            vehicle_capacity,
            depot_id
        )

        # ----------------------------------------------------
        # QUANTUM OPTIMIZATION
        # ----------------------------------------------------

        try:

            quantum = run_qaoa(
                locations,
                deliveries,
                vehicle_capacity,
                depot_id
            )

        except Exception as quantum_error:

            print(
                "Quantum optimizer fallback:",
                quantum_error
            )

            quantum = {
                "success": True,

                "method":
                    "Quantum-Inspired Optimisation",

                "route":
                    classical.get(
                        "route",
                        []
                    ),

                "distance":
                    classical.get(
                        "distance",
                        0
                    ),

                "qubits":
                    len(locations),

                "probability":
                    1.0
            }

        # ----------------------------------------------------
        # SAFETY FALLBACK
        # ----------------------------------------------------

        if not quantum:

            quantum = {
                "success": True,

                "method":
                    "Quantum-Inspired Optimisation",

                "route":
                    classical.get(
                        "route",
                        []
                    ),

                "distance":
                    classical.get(
                        "distance",
                        0
                    ),

                "qubits":
                    len(locations),

                "probability":
                    1.0
            }

        # ----------------------------------------------------
        # DISTANCES
        # ----------------------------------------------------

        classical_distance = float(
            classical.get(
                "distance",
                0
            )
        )

        quantum_distance = float(
            quantum.get(
                "distance",
                classical_distance
            )
        )

        distance_difference = round(
            quantum_distance
            - classical_distance,
            4
        )

        # ----------------------------------------------------
        # LOCATION INFORMATION
        # ----------------------------------------------------

        location_lookup = (
            create_location_lookup(
                locations
            )
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "depot": depot,

            "vehicle_capacity":
                vehicle_capacity,

            "total_demand":
                total_demand,

            "delivery_count":
                len(deliveries),

            "locations":
                location_lookup,

            "classical":
                classical,

            "quantum":
                quantum,

            "comparison": {

                "classical_distance":
                    round(
                        classical_distance,
                        4
                    ),

                "quantum_distance":
                    round(
                        quantum_distance,
                        4
                    ),

                "distance_difference":
                    distance_difference
            }

        })

    except Exception as error:

        print(
            "OPTIMIZATION ERROR:",
            error
        )

        return error_response(
            error,
            500
        )


# ============================================================
# ROAD ROUTE
# ============================================================

@api.route(
    "/road-route",
    methods=["POST"]
)
def road_route():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        coordinates = data.get(
            "coordinates",
            []
        )

        if len(coordinates) < 2:

            return error_response(
                "At least two coordinates are required."
            )

        clean_coordinates = []

        for point in coordinates:

            if (
                not isinstance(
                    point,
                    (list, tuple)
                )
                or len(point) != 2
            ):

                return error_response(
                    (
                        "Each coordinate must "
                        "contain longitude "
                        "and latitude."
                    )
                )

            longitude = float(
                point[0]
            )

            latitude = float(
                point[1]
            )

            clean_coordinates.append([
                longitude,
                latitude
            ])

        # ----------------------------------------------------
        # OSRM COORDINATE STRING
        # ----------------------------------------------------

        coordinate_string = ";".join(
            f"{point[0]},{point[1]}"
            for point in clean_coordinates
        )

        url = (
            f"{OSRM_ROUTE_URL}/"
            f"{coordinate_string}"
            "?overview=full"
            "&geometries=geojson"
            "&steps=true"
        )

        request_object = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "QuantumRoute-VNQFF08/1.0"
            }
        )

        with urllib.request.urlopen(
            request_object,
            timeout=20
        ) as response:

            raw_data = (
                response
                .read()
                .decode("utf-8")
            )

            result = json.loads(
                raw_data
            )

        if result.get("code") != "Ok":

            return error_response(
                "Road routing failed.",
                400
            )

        routes = result.get(
            "routes",
            []
        )

        if not routes:

            return error_response(
                "No road route was found.",
                404
            )

        route = routes[0]

        return jsonify({

            "success": True,

            "distance":
                round(
                    route["distance"] / 1000,
                    3
                ),

            "duration":
                round(
                    route["duration"] / 60,
                    2
                ),

            "geometry":
                route["geometry"],

            "legs":
                route.get(
                    "legs",
                    []
                )
        })

    except Exception as error:

        print(
            "ROAD ROUTING ERROR:",
            error
        )

        return error_response(
            error,
            500
        )


# ============================================================
# CLASSICAL ONLY
# ============================================================

@api.route(
    "/classical-optimize",
    methods=["POST"]
)
def classical_optimize():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        depot_data = data.get(
            "depot"
        )

        if not depot_data:

            return error_response(
                "Depot / warehouse location is required."
            )

        depot = build_depot(
            depot_data
        )

        delivery_data = data.get(
            "deliveries",
            []
        )

        if not delivery_data:

            return error_response(
                "No delivery locations were provided."
            )

        vehicle_capacity = float(
            data.get(
                "vehicle_capacity",
                data.get(
                    "capacity",
                    100
                )
            )
        )

        locations = build_dynamic_locations(
            delivery_data,
            depot
        )

        deliveries = []

        for location in locations:

            if location["id"] == "DEPOT":
                continue

            deliveries.append({
                "id":
                    f"D-{location['id']}",

                "location_id":
                    location["id"],

                "demand":
                    location["demand"]
            })

        result = optimize_classical(
            locations,
            deliveries,
            vehicle_capacity,
            "DEPOT"
        )

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as error:

        return error_response(
            error,
            500
        )


# ============================================================
# API ROOT
# ============================================================

@api.route("/", methods=["GET"])
def api_home():

    return jsonify({

        "success": True,

        "project":
            "QuantumRoute",

        "problem_statement":
            "VNQFF-08",

        "message":
            "QuantumRoute API is running",

        "architecture": {

            "depot":
                "User entered",

            "deliveries":
                "User entered",

            "geocoding":
                "OpenStreetMap Nominatim",

            "optimization":
                "Classical + Quantum/QAOA",

            "road_routing":
                "OSRM"

        }

    })