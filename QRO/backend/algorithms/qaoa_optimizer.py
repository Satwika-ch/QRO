"""
QuantumRoute - QAOA Optimizer
Problem Statement: VNQFF-08

Features:
- OSRM driving distance with Euclidean fallback
- Shared distance matrix
- Multi-objective route scoring
- State-vector QAOA-style simulation
- Reproducible measurement sampling
- Quantum-inspired fallback for larger problems
"""

import itertools
import json
import math
import urllib.request

import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

QAOA_SHOTS = 1000
BETA_STEPS = 20
GAMMA_STEPS = 20

AVERAGE_SPEED_KMPH = 40.0
FUEL_RATE_L_PER_KM = 0.08
FUEL_PRICE_PER_L = 100.0
TIME_COST_PER_HOUR = 500.0

DISTANCE_WEIGHT = 0.40
TIME_WEIGHT = 0.25
FUEL_WEIGHT = 0.15
COST_WEIGHT = 0.20

OSRM_TIMEOUT = 20
RANDOM_SEED = 42


# ============================================================
# DISTANCE
# ============================================================

def euclidean_distance(point_a, point_b):
    x1, y1 = point_a
    x2, y2 = point_b
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def road_distance_km(
    latitude_a,
    longitude_a,
    latitude_b,
    longitude_b,
):
    """Return OSRM directional driving distance in kilometres."""
    coordinates = (
        f"{longitude_a},{latitude_a};"
        f"{longitude_b},{latitude_b}"
    )
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{coordinates}?overview=false"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "QuantumRoute/1.0"},
        )

        with urllib.request.urlopen(
            request,
            timeout=OSRM_TIMEOUT,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") != "Ok":
            return None

        routes = data.get("routes", [])
        if not routes:
            return None

        distance = float(routes[0]["distance"]) / 1000.0
        return distance if math.isfinite(distance) else None

    except Exception as error:
        print("OSRM routing failed; using fallback:", error)
        return None


def _fallback_distance(location_a, location_b):
    """Use x/y when available; otherwise use approximate geographic distance."""
    if all(
        key in location_a and key in location_b
        for key in ("x", "y")
    ):
        return euclidean_distance(
            (
                float(location_a["x"]),
                float(location_a["y"]),
            ),
            (
                float(location_b["x"]),
                float(location_b["y"]),
            ),
        )

    if all(
        location_a.get(key) is not None
        and location_b.get(key) is not None
        for key in ("lat", "lon")
    ):
        lat1 = math.radians(float(location_a["lat"]))
        lon1 = math.radians(float(location_a["lon"]))
        lat2 = math.radians(float(location_b["lat"]))
        lon2 = math.radians(float(location_b["lon"]))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )
        a = min(1.0, max(0.0, a))
        return 6371.0 * 2.0 * math.asin(math.sqrt(a))

    raise ValueError(
        "Each location needs lat/lon or x/y coordinates."
    )


def build_distance_matrix(locations):
    """
    Build a directional matrix once per optimization request.
    All algorithms should reuse this matrix for a fair comparison.
    """
    if not locations:
        raise ValueError("Locations are required.")

    n = len(locations)
    matrix = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            a = locations[i]
            b = locations[j]
            road_distance = None

            if all(
                item.get(key) is not None
                for item in (a, b)
                for key in ("lat", "lon")
            ):
                road_distance = road_distance_km(
                    float(a["lat"]),
                    float(a["lon"]),
                    float(b["lat"]),
                    float(b["lon"]),
                )

            if road_distance is None:
                road_distance = _fallback_distance(a, b)

            if (
                not math.isfinite(road_distance)
                or road_distance < 0
            ):
                raise ValueError(
                    f"Invalid distance between {a.get('id')} "
                    f"and {b.get('id')}."
                )

            matrix[i, j] = road_distance

    return matrix


# ============================================================
# ROUTE DISTANCE AND METRICS
# ============================================================

def route_distance(route, distance_matrix):
    matrix = np.asarray(distance_matrix, dtype=float)

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Distance matrix must be square.")

    if not route or len(route) < 2:
        raise ValueError("Route must contain a start and end location.")

    total = 0.0

    for i in range(len(route) - 1):
        start = int(route[i])
        end = int(route[i + 1])

        if (
            start < 0
            or end < 0
            or start >= matrix.shape[0]
            or end >= matrix.shape[0]
        ):
            raise ValueError("Route contains an invalid location index.")

        total += matrix[start, end]

    return float(total)


def calculate_route_metrics(route, distance_matrix):
    distance = route_distance(route, distance_matrix)

    time_hours = distance / AVERAGE_SPEED_KMPH
    fuel_litres = distance * FUEL_RATE_L_PER_KM
    fuel_cost = fuel_litres * FUEL_PRICE_PER_L
    operational_cost = time_hours * TIME_COST_PER_HOUR
    total_cost = fuel_cost + operational_cost

    return {
        "distance": round(distance, 2),
        "time": round(time_hours, 2),
        "time_hours": round(time_hours, 2),
        "fuel": round(fuel_litres, 2),
        "fuel_litres": round(fuel_litres, 2),
        "fuel_cost": round(fuel_cost, 2),
        "operational_cost": round(operational_cost, 2),
        "cost": round(total_cost, 2),
    }


# ============================================================
# ROUTE VALIDATION AND GENERATION
# ============================================================

def is_valid_route(route, number_of_locations, depot_index=0):
    if not route:
        return False

    if route[0] != depot_index or route[-1] != depot_index:
        return False

    deliveries = route[1:-1]
    expected = set(range(number_of_locations))
    expected.discard(depot_index)

    return (
        len(deliveries) == len(expected)
        and set(deliveries) == expected
        and len(deliveries) == len(set(deliveries))
    )


def generate_valid_routes(number_of_locations, depot_index=0):
    if number_of_locations < 2:
        return []

    delivery_indices = [
        i for i in range(number_of_locations)
        if i != depot_index
    ]

    return [
        [depot_index, *permutation, depot_index]
        for permutation in itertools.permutations(delivery_indices)
    ]


# ============================================================
# MULTI-OBJECTIVE SCORING
# ============================================================

def _normalize(values):
    values = np.asarray(values, dtype=float)

    if values.size == 0:
        return values

    minimum = float(np.min(values))
    maximum = float(np.max(values))

    if maximum - minimum < 1e-12:
        return np.zeros_like(values)

    return (values - minimum) / (maximum - minimum)


def calculate_objective_from_metrics(
    metrics,
    distance_min,
    distance_max,
    time_min,
    time_max,
    fuel_min,
    fuel_max,
    cost_min,
    cost_max,
):
    def scale(value, minimum, maximum):
        if maximum - minimum < 1e-12:
            return 0.0
        return (value - minimum) / (maximum - minimum)

    return float(
        DISTANCE_WEIGHT * scale(
            metrics["distance"], distance_min, distance_max
        )
        + TIME_WEIGHT * scale(
            metrics["time_hours"], time_min, time_max
        )
        + FUEL_WEIGHT * scale(
            metrics["fuel_litres"], fuel_min, fuel_max
        )
        + COST_WEIGHT * scale(
            metrics["cost"], cost_min, cost_max
        )
    )


def evaluate_routes(routes, distance_matrix):
    if not routes:
        return []

    all_metrics = [
        calculate_route_metrics(route, distance_matrix)
        for route in routes
    ]

    distances = [item["distance"] for item in all_metrics]
    times = [item["time_hours"] for item in all_metrics]
    fuels = [item["fuel_litres"] for item in all_metrics]
    costs = [item["cost"] for item in all_metrics]

    bounds = (
        min(distances), max(distances),
        min(times), max(times),
        min(fuels), max(fuels),
        min(costs), max(costs),
    )

    evaluated = []

    for route, metrics in zip(routes, all_metrics):
        objective = calculate_objective_from_metrics(
            metrics, *bounds
        )
        evaluated.append({
            "route": route,
            "metrics": metrics,
            "objective": objective,
        })

    return evaluated


def select_best_feasible_route(evaluated_routes):
    if not evaluated_routes:
        return None

    return min(
        evaluated_routes,
        key=lambda item: (
            item["objective"],
            item["metrics"]["distance"],
            tuple(item["route"]),
        ),
    )


def build_route_costs(routes, distance_matrix):
    if not routes:
        return np.asarray([], dtype=float)

    metrics = [
        calculate_route_metrics(route, distance_matrix)
        for route in routes
    ]

    distances = _normalize([item["distance"] for item in metrics])
    times = _normalize([item["time_hours"] for item in metrics])
    fuels = _normalize([item["fuel_litres"] for item in metrics])
    costs = _normalize([item["cost"] for item in metrics])

    return np.asarray(
        DISTANCE_WEIGHT * distances
        + TIME_WEIGHT * times
        + FUEL_WEIGHT * fuels
        + COST_WEIGHT * costs,
        dtype=float,
    )


def normalize_costs(costs):
    return _normalize(costs)


# ============================================================
# MIXER AND QAOA STATE
# ============================================================

def build_mixer_matrix(routes):
    count = len(routes)
    mixer = np.zeros((count, count), dtype=float)

    for i in range(count):
        for j in range(i + 1, count):
            route_a = routes[i][1:-1]
            route_b = routes[j][1:-1]

            differences = [
                pos for pos in range(len(route_a))
                if route_a[pos] != route_b[pos]
            ]

            # Connect routes differing by one adjacent swap.
            if len(differences) == 2:
                first, second = differences
                if abs(first - second) == 1:
                    mixer[i, j] = 1.0
                    mixer[j, i] = 1.0

    return mixer


def matrix_exponential(matrix):
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    return (
        eigenvectors
        @ np.diag(np.exp(eigenvalues))
        @ eigenvectors.T
    )


def apply_route_cost_phase(state, normalized_costs, gamma):
    return state * np.exp(-1j * gamma * normalized_costs)


def apply_route_mixer(state, mixer_matrix, beta):
    if mixer_matrix.shape[0] <= 1:
        return state.copy()

    eigenvalues, eigenvectors = np.linalg.eigh(mixer_matrix)
    phases = np.exp(-1j * beta * eigenvalues)
    unitary = (eigenvectors * phases) @ eigenvectors.conj().T

    return unitary @ state


def initial_uniform_state(number_of_routes):
    if number_of_routes <= 0:
        return np.array([], dtype=np.complex128)

    return (
        np.ones(number_of_routes, dtype=np.complex128)
        / math.sqrt(number_of_routes)
    )


def run_qaoa_state(normalized_costs, mixer_matrix, beta, gamma):
    state = initial_uniform_state(len(normalized_costs))
    state = apply_route_cost_phase(state, normalized_costs, gamma)
    state = apply_route_mixer(state, mixer_matrix, beta)

    norm = np.linalg.norm(state)
    if norm > 0:
        state = state / norm

    return state


def expectation_value(state, normalized_costs):
    probabilities = np.abs(state) ** 2
    return float(np.sum(probabilities * normalized_costs))


def optimize_qaoa_parameters(normalized_costs, mixer_matrix):
    best_beta = 0.0
    best_gamma = 0.0
    best_expectation = float("inf")

    betas = np.linspace(0.0, math.pi, BETA_STEPS)
    gammas = np.linspace(0.0, math.pi, GAMMA_STEPS)

    for beta in betas:
        for gamma in gammas:
            state = run_qaoa_state(
                normalized_costs,
                mixer_matrix,
                beta,
                gamma,
            )
            expectation = expectation_value(state, normalized_costs)

            if expectation < best_expectation - 1e-12:
                best_expectation = expectation
                best_beta = float(beta)
                best_gamma = float(gamma)

    return best_beta, best_gamma, best_expectation


# ============================================================
# PROBABILITIES AND DETERMINISTIC MEASUREMENT
# ============================================================

def get_route_probabilities(state, routes):
    probabilities = np.abs(state) ** 2
    results = []

    for index, route in enumerate(routes):
        results.append({
            "index": index,
            "route": route,
            "probability": float(probabilities[index]),
        })

    return sorted(
        results,
        key=lambda item: (-item["probability"], item["index"]),
    )


def sample_quantum_routes(state, routes, shots=QAOA_SHOTS):
    """
    Simulated measurement using a fixed random seed.
    The same state and shots produce repeatable measurement results.
    """
    probabilities = np.abs(state) ** 2
    total_probability = float(np.sum(probabilities))

    if total_probability <= 0 or not routes or shots <= 0:
        return []

    probabilities = probabilities / total_probability
    rng = np.random.default_rng(RANDOM_SEED)

    samples = rng.choice(
        len(routes),
        size=shots,
        p=probabilities,
    )

    counts = {}
    for index in samples:
        index = int(index)
        counts[index] = counts.get(index, 0) + 1

    measured = []

    for index, count in counts.items():
        measured.append({
            "index": index,
            "route": routes[index],
            "count": count,
            "measured_probability": float(count / shots),
            "qaoa_probability": float(probabilities[index]),
        })

    return sorted(
        measured,
        key=lambda item: (-item["count"], item["index"]),
    )


def select_quantum_route(
    state,
    routes,
    distance_matrix,
    shots=QAOA_SHOTS,
):
    if not routes:
        return None, 0.0, None, []

    probabilities = np.abs(state) ** 2
    total_probability = float(np.sum(probabilities))

    if total_probability <= 0:
        return None, 0.0, None, []

    probabilities = probabilities / total_probability
    measured_routes = sample_quantum_routes(state, routes, shots)

    if not measured_routes:
        return None, 0.0, None, []

    evaluated = evaluate_routes(routes, distance_matrix)
    evaluated_by_index = {
        index: item for index, item in enumerate(evaluated)
    }

    candidates = []

    for item in measured_routes:
        index = int(item["index"])
        candidate = evaluated_by_index.get(index)

        if candidate is None:
            continue

        candidates.append({
            "index": index,
            "route": candidate["route"],
            "metrics": candidate["metrics"],
            "objective": candidate["objective"],
            "count": item["count"],
            "qaoa_probability": float(probabilities[index]),
            "measured_probability": item["measured_probability"],
        })

    if not candidates:
        return None, 0.0, None, measured_routes

    selected = min(
        candidates,
        key=lambda item: (
            item["objective"],
            item["metrics"]["distance"],
            tuple(item["route"]),
        ),
    )

    return (
        selected["route"],
        float(probabilities[selected["index"]]),
        int(selected["index"]),
        measured_routes,
    )


# ============================================================
# DEPOT / DEMAND HELPERS
# ============================================================

def _prepare_locations_and_matrix(
    locations,
    depot_id,
    distance_matrix=None,
):
    """Ensure depot is index 0 and keep the matrix in matching order."""
    if not locations:
        raise ValueError("No locations supplied.")

    depot_index = next(
        (
            index for index, location in enumerate(locations)
            if location.get("id") == depot_id
        ),
        None,
    )

    if depot_index is None:
        raise ValueError(f"{depot_id} location not found.")

    locations = list(locations)

    if distance_matrix is None:
        distance_matrix = build_distance_matrix(locations)
    else:
        distance_matrix = np.asarray(distance_matrix, dtype=float)

        expected_shape = (len(locations), len(locations))
        if distance_matrix.shape != expected_shape:
            raise ValueError(
                "Distance matrix dimensions do not match locations."
            )

    if depot_index != 0:
        order = [depot_index] + [
            index for index in range(len(locations))
            if index != depot_index
        ]
        locations = [locations[index] for index in order]
        distance_matrix = distance_matrix[np.ix_(order, order)]

    return locations, distance_matrix


def _total_demand(deliveries):
    try:
        total = sum(
            float(delivery.get("demand", 0))
            for delivery in (deliveries or [])
        )
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("Invalid delivery demand.") from error

    if not math.isfinite(total) or total < 0:
        raise ValueError("Delivery demand must be finite and non-negative.")

    return total


def _failure(message, **extra):
    result = {
        "success": False,
        "error": message,
    }
    result.update(extra)
    return result


# ============================================================
# SMALL QAOA
# ============================================================

def run_small_qaoa(
    locations,
    deliveries=None,
    vehicle_capacity=None,
    depot_id="DEPOT",
    distance_matrix=None,
):
    try:
        locations, distance_matrix = _prepare_locations_and_matrix(
            locations,
            depot_id,
            distance_matrix,
        )
        total_demand = _total_demand(deliveries)

        if vehicle_capacity is not None:
            capacity = float(vehicle_capacity)
            if not math.isfinite(capacity) or capacity <= 0:
                return _failure("Vehicle capacity must be positive.")

            if total_demand > capacity:
                return _failure(
                    "Vehicle capacity exceeded.",
                    total_demand=total_demand,
                    vehicle_capacity=capacity,
                )

    except (ValueError, TypeError) as error:
        return _failure(str(error))

    routes = generate_valid_routes(
        len(locations),
        depot_index=0,
    )

    if not routes:
        return _failure("No valid routes found.")

    route_costs = build_route_costs(routes, distance_matrix)
    normalized_costs = normalize_costs(route_costs)
    mixer_matrix = build_mixer_matrix(routes)

    beta, gamma, expected_energy = optimize_qaoa_parameters(
        normalized_costs,
        mixer_matrix,
    )

    state = run_qaoa_state(
        normalized_costs,
        mixer_matrix,
        beta,
        gamma,
    )

    (
        quantum_route,
        probability,
        selected_index,
        measured_routes,
    ) = select_quantum_route(
        state,
        routes,
        distance_matrix,
        QAOA_SHOTS,
    )

    if quantum_route is None:
        return _failure("QAOA measurement failed.")

    if not is_valid_route(
        quantum_route,
        len(locations),
        depot_index=0,
    ):
        return _failure("Internal QAOA route validation failed.")

    metrics = calculate_route_metrics(
        quantum_route,
        distance_matrix,
    )

    evaluated_routes = evaluate_routes(routes, distance_matrix)
    objective = next(
        (
            item["objective"]
            for item in evaluated_routes
            if item["route"] == quantum_route
        ),
        0.0,
    )

    route_probabilities = get_route_probabilities(state, routes)

    measured_route_output = [
        {
            "route": [
                locations[index]["id"]
                for index in item["route"]
            ],
            "count": item["count"],
            "measured_probability": round(
                item["measured_probability"], 4
            ),
            "qaoa_probability": round(
                item["qaoa_probability"], 8
            ),
        }
        for item in measured_routes
    ]

    return {
        "success": True,
        "route": [
            locations[index]["id"]
            for index in quantum_route
        ],
        **metrics,
        "objective": round(float(objective), 6),
        "probability": round(float(probability), 8),
        "probability_percent": round(float(probability) * 100, 4),
        "selected_route_index": selected_index,
        "number_of_feasible_routes": len(routes),
        "qubits": len(locations) * len(locations),
        "shots": QAOA_SHOTS,
        "beta": round(beta, 6),
        "gamma": round(gamma, 6),
        "expected_energy": round(float(expected_energy), 6),
        "total_demand": round(total_demand, 2),
        "route_probabilities": [
            {
                "route": [
                    locations[index]["id"]
                    for index in item["route"]
                ],
                "probability": round(item["probability"], 8),
                "probability_percent": round(
                    item["probability"] * 100, 4
                ),
            }
            for item in route_probabilities
        ],
        "measured_routes": measured_route_output,
        "method": (
            "QAOA p=1 Multi-Objective Feasible-Route "
            "State-Vector Simulation + Measurement-Based Decoding"
        ),
        "message": (
            "QAOA simulation completed. The best measured feasible "
            "route was selected from the simulated probability distribution."
        ),
    }


# ============================================================
# QUANTUM-INSPIRED FALLBACK
# ============================================================

def run_quantum_inspired(
    locations,
    deliveries=None,
    vehicle_capacity=None,
    depot_id="DEPOT",
    distance_matrix=None,
):
    try:
        locations, distance_matrix = _prepare_locations_and_matrix(
            locations,
            depot_id,
            distance_matrix,
        )
        total_demand = _total_demand(deliveries)

        if vehicle_capacity is not None:
            capacity = float(vehicle_capacity)
            if not math.isfinite(capacity) or capacity <= 0:
                return _failure("Vehicle capacity must be positive.")

            if total_demand > capacity:
                return _failure(
                    "Vehicle capacity exceeded.",
                    total_demand=total_demand,
                    vehicle_capacity=capacity,
                )

    except (ValueError, TypeError) as error:
        return _failure(str(error))

    routes = generate_valid_routes(
        len(locations),
        depot_index=0,
    )

    if not routes:
        return _failure("No valid routes found.")

    evaluated = evaluate_routes(routes, distance_matrix)
    best = select_best_feasible_route(evaluated)

    if best is None:
        return _failure("Unable to select a feasible route.")

    return {
        "success": True,
        "route": [
            locations[index]["id"]
            for index in best["route"]
        ],
        **best["metrics"],
        "objective": round(float(best["objective"]), 6),
        "probability": 1.0,
        "probability_percent": 100.0,
        "qubits": 0,
        "shots": 0,
        "beta": 0.0,
        "gamma": 0.0,
        "total_demand": round(total_demand, 2),
        "method": "Quantum-Inspired Optimization Fallback",
        "message": (
            "The route was selected using a deterministic "
            "quantum-inspired classical fallback, not a QAOA state-vector run."
        ),
    }


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def run_qaoa(
    locations,
    deliveries=None,
    vehicle_capacity=None,
    depot_id="DEPOT",
    distance_matrix=None,
):
    """
    Public optimizer entry point.

    The coordinator can pass its shared matrix. If it does not,
    this function builds one matrix and reuses it internally.
    """
    if not locations:
        return _failure("No locations supplied.")

    if distance_matrix is None:
        try:
            distance_matrix = build_distance_matrix(locations)
        except Exception as error:
            return _failure(f"Unable to build distance matrix: {error}")

    if len(locations) <= 5:
        return run_small_qaoa(
            locations=locations,
            deliveries=deliveries,
            vehicle_capacity=vehicle_capacity,
            depot_id=depot_id,
            distance_matrix=distance_matrix,
        )

    return run_quantum_inspired(
        locations=locations,
        deliveries=deliveries,
        vehicle_capacity=vehicle_capacity,
        depot_id=depot_id,
        distance_matrix=distance_matrix,
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":
    locations = [
        {
            "id": "DEPOT",
            "x": 0.0,
            "y": 0.0,
            "lat": 16.5115306,
            "lon": 80.6160469,
        },
        {
            "id": "D001",
            "x": 100.0,
            "y": 50.0,
            "lat": 14.449918,
            "lon": 79.986967,
        },
        {
            "id": "D002",
            "x": 250.0,
            "y": 180.0,
            "lat": 16.713114,
            "lon": 81.104365,
        },
        {
            "id": "D003",
            "x": -80.0,
            "y": 120.0,
            "lat": 16.299737,
            "lon": 80.457293,
        },
    ]

    deliveries = [
        {"id": "D001", "demand": 20},
        {"id": "D002", "demand": 15},
        {"id": "D003", "demand": 17},
    ]

    matrix = build_distance_matrix(locations)

    result = run_qaoa(
        locations=locations,
        deliveries=deliveries,
        vehicle_capacity=100,
        depot_id="DEPOT",
        distance_matrix=matrix,
    )

    print("=" * 60)
    print("QUANTUMROUTE QAOA TEST")
    print("=" * 60)
    print("Success:", result.get("success"))
    print("Error:", result.get("error"))
    print("Route:", result.get("route"))
    print("Distance:", result.get("distance"), "km")
    print("Time:", result.get("time"), "hours")
    print("Fuel:", result.get("fuel"), "litres")
    print("Cost:", result.get("cost"), "INR")
    print("Method:", result.get("method"))
    print("=" * 60)