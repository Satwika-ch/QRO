"""
QuantumRoute - QAOA Optimizer

Problem Statement:
VNQFF-08

Application:
Quantum-Enhanced Last-Mile Route Optimisation

Features:
    - State-vector QAOA-style simulation
    - Real road distance using OSRM
    - Euclidean fallback when OSRM is unavailable
    - Multi-objective optimisation
    - Feasible-route quantum state
    - Measurement-based quantum candidate generation
    - Best measured feasible candidate selected
    - Depot fixed as first and last location
"""

import itertools
import math
import json
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

OSRM_TIMEOUT = 10


# ============================================================
# DISTANCE
# ============================================================

def euclidean_distance(point_a, point_b):

    x1, y1 = point_a
    x2, y2 = point_b

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


def road_distance_km(
    latitude_a,
    longitude_a,
    latitude_b,
    longitude_b
):
    """
    Get directional driving distance from OSRM.

    OSRM format:
        longitude,latitude

    Returns:
        distance in kilometres
    """

    coordinates = (
        f"{longitude_a},{latitude_a};"
        f"{longitude_b},{latitude_b}"
    )

    url = (
        "https://router.project-osrm.org/"
        "route/v1/driving/"
        + coordinates
        + "?overview=false"
    )

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "QuantumRoute/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=OSRM_TIMEOUT
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        if data.get("code") != "Ok":
            return None

        routes = data.get(
            "routes",
            []
        )

        if not routes:
            return None

        return (
            float(routes[0]["distance"])
            / 1000.0
        )

    except Exception as error:

        print(
            "OSRM routing failed:",
            error
        )

        return None


def build_distance_matrix(locations):
    """
    Build directional road-distance matrix.

    OSRM is used when lat/lon are available.
    Euclidean x/y distance is used as fallback.
    """

    n = len(locations)

    matrix = np.zeros(
        (n, n),
        dtype=float
    )

    for i in range(n):

        for j in range(n):

            if i == j:
                continue

            location_a = locations[i]
            location_b = locations[j]

            latitude_a = location_a.get("lat")
            longitude_a = location_a.get("lon")

            latitude_b = location_b.get("lat")
            longitude_b = location_b.get("lon")

            road_distance = None

            if (
                latitude_a is not None
                and longitude_a is not None
                and latitude_b is not None
                and longitude_b is not None
            ):

                road_distance = road_distance_km(
                    float(latitude_a),
                    float(longitude_a),
                    float(latitude_b),
                    float(longitude_b)
                )

            if road_distance is not None:

                matrix[i, j] = road_distance

            else:

                point_a = (
                    float(location_a["x"]),
                    float(location_a["y"])
                )

                point_b = (
                    float(location_b["x"]),
                    float(location_b["y"])
                )

                matrix[i, j] = euclidean_distance(
                    point_a,
                    point_b
                )

    return matrix


# ============================================================
# ROUTE DISTANCE
# ============================================================

def route_distance(
    route,
    distance_matrix
):

    total = 0.0

    for i in range(
        len(route) - 1
    ):

        total += distance_matrix[
            route[i],
            route[i + 1]
        ]

    return float(total)


# ============================================================
# ROUTE METRICS
# ============================================================

def calculate_route_metrics(
    route,
    distance_matrix
):

    distance = route_distance(
        route,
        distance_matrix
    )

    time_hours = (
        distance /
        AVERAGE_SPEED_KMPH
    )

    fuel_litres = (
        distance *
        FUEL_RATE_L_PER_KM
    )

    fuel_cost = (
        fuel_litres *
        FUEL_PRICE_PER_L
    )

    operational_cost = (
        time_hours *
        TIME_COST_PER_HOUR
    )

    total_cost = (
        fuel_cost +
        operational_cost
    )

    return {

        "distance":
            round(distance, 2),

        "time":
            round(time_hours, 2),

        "time_hours":
            round(time_hours, 2),

        "fuel":
            round(fuel_litres, 2),

        "fuel_litres":
            round(fuel_litres, 2),

        "fuel_cost":
            round(fuel_cost, 2),

        "operational_cost":
            round(operational_cost, 2),

        "cost":
            round(total_cost, 2)
    }


# ============================================================
# ROUTE VALIDATION
# ============================================================

def is_valid_route(
    route,
    number_of_locations,
    depot_index=0
):

    if not route:
        return False

    if route[0] != depot_index:
        return False

    if route[-1] != depot_index:
        return False

    deliveries = route[1:-1]

    expected = set(
        range(number_of_locations)
    )

    expected.discard(
        depot_index
    )

    if len(deliveries) != len(expected):
        return False

    if set(deliveries) != expected:
        return False

    if len(deliveries) != len(set(deliveries)):
        return False

    return True


# ============================================================
# GENERATE VALID ROUTES
# ============================================================

def generate_valid_routes(
    number_of_locations,
    depot_index=0
):

    delivery_indices = [

        i

        for i in range(
            number_of_locations
        )

        if i != depot_index
    ]

    routes = []

    for permutation in itertools.permutations(
        delivery_indices
    ):

        route = [
            depot_index,
            *permutation,
            depot_index
        ]

        if is_valid_route(
            route,
            number_of_locations,
            depot_index
        ):

            routes.append(route)

    return routes


# ============================================================
# OBJECTIVE
# ============================================================

def calculate_objective_from_metrics(
    metrics,
    distance_min,
    distance_max,
    time_min,
    time_max,
    fuel_min,
    fuel_max,
    cost_min,
    cost_max
):

    def scale(
        value,
        minimum,
        maximum
    ):

        if (
            maximum - minimum
            < 1e-12
        ):
            return 0.0

        return (
            value - minimum
        ) / (
            maximum - minimum
        )

    distance_score = scale(
        metrics["distance"],
        distance_min,
        distance_max
    )

    time_score = scale(
        metrics["time_hours"],
        time_min,
        time_max
    )

    fuel_score = scale(
        metrics["fuel_litres"],
        fuel_min,
        fuel_max
    )

    cost_score = scale(
        metrics["cost"],
        cost_min,
        cost_max
    )

    return float(

        DISTANCE_WEIGHT *
        distance_score

        +

        TIME_WEIGHT *
        time_score

        +

        FUEL_WEIGHT *
        fuel_score

        +

        COST_WEIGHT *
        cost_score
    )


# ============================================================
# EVALUATE ROUTES
# ============================================================

def evaluate_routes(
    routes,
    distance_matrix
):

    if not routes:
        return []

    all_metrics = [

        calculate_route_metrics(
            route,
            distance_matrix
        )

        for route in routes
    ]

    distances = [
        item["distance"]
        for item in all_metrics
    ]

    times = [
        item["time_hours"]
        for item in all_metrics
    ]

    fuels = [
        item["fuel_litres"]
        for item in all_metrics
    ]

    costs = [
        item["cost"]
        for item in all_metrics
    ]

    distance_min = min(distances)
    distance_max = max(distances)

    time_min = min(times)
    time_max = max(times)

    fuel_min = min(fuels)
    fuel_max = max(fuels)

    cost_min = min(costs)
    cost_max = max(costs)

    evaluated = []

    for route, metrics in zip(
        routes,
        all_metrics
    ):

        objective = calculate_objective_from_metrics(

            metrics,

            distance_min,
            distance_max,

            time_min,
            time_max,

            fuel_min,
            fuel_max,

            cost_min,
            cost_max
        )

        evaluated.append({

            "route": route,

            "metrics": metrics,

            "objective": objective
        })

    return evaluated


# ============================================================
# BEST FEASIBLE ROUTE
# ============================================================

def select_best_feasible_route(
    evaluated_routes
):

    if not evaluated_routes:
        return None

    return min(
        evaluated_routes,
        key=lambda item:
        item["objective"]
    )


# ============================================================
# QUANTUM ROUTE COST
# ============================================================

def build_route_costs(
    routes,
    distance_matrix
):

    if not routes:

        return np.asarray(
            [],
            dtype=float
        )

    all_metrics = [

        calculate_route_metrics(
            route,
            distance_matrix
        )

        for route in routes
    ]

    distances = np.array(
        [
            item["distance"]
            for item in all_metrics
        ],
        dtype=float
    )

    times = np.array(
        [
            item["time_hours"]
            for item in all_metrics
        ],
        dtype=float
    )

    fuels = np.array(
        [
            item["fuel_litres"]
            for item in all_metrics
        ],
        dtype=float
    )

    costs = np.array(
        [
            item["cost"]
            for item in all_metrics
        ],
        dtype=float
    )

    def normalize(values):

        minimum = np.min(values)
        maximum = np.max(values)

        if (
            maximum - minimum
            < 1e-12
        ):

            return np.zeros_like(
                values
            )

        return (
            values - minimum
        ) / (
            maximum - minimum
        )

    distance_score = normalize(
        distances
    )

    time_score = normalize(
        times
    )

    fuel_score = normalize(
        fuels
    )

    cost_score = normalize(
        costs
    )

    objective = (

        DISTANCE_WEIGHT *
        distance_score

        +

        TIME_WEIGHT *
        time_score

        +

        FUEL_WEIGHT *
        fuel_score

        +

        COST_WEIGHT *
        cost_score
    )

    return np.asarray(
        objective,
        dtype=float
    )


# ============================================================
# NORMALIZE
# ============================================================

def normalize_costs(
    costs
):

    costs = np.asarray(
        costs,
        dtype=float
    )

    if len(costs) == 0:
        return costs

    minimum = np.min(costs)
    maximum = np.max(costs)

    if (
        maximum - minimum
        < 1e-12
    ):

        return np.zeros_like(
            costs
        )

    return (
        costs - minimum
    ) / (
        maximum - minimum
    )


# ============================================================
# MIXER
# ============================================================

def build_mixer_matrix(
    routes
):

    number_of_routes = len(
        routes
    )

    mixer = np.zeros(
        (
            number_of_routes,
            number_of_routes
        ),
        dtype=float
    )

    for i in range(
        number_of_routes
    ):

        for j in range(
            i + 1,
            number_of_routes
        ):

            route_a = routes[i][1:-1]
            route_b = routes[j][1:-1]

            differences = [

                position

                for position in range(
                    len(route_a)
                )

                if (
                    route_a[position]
                    !=
                    route_b[position]
                )
            ]

            if len(differences) == 2:

                first = differences[0]
                second = differences[1]

                if abs(
                    first - second
                ) == 1:

                    mixer[i, j] = 1.0
                    mixer[j, i] = 1.0

    return mixer


# ============================================================
# MATRIX EXPONENTIAL
# ============================================================

def matrix_exponential(
    matrix
):

    eigenvalues, eigenvectors = np.linalg.eigh(
        matrix
    )

    diagonal = np.diag(
        np.exp(eigenvalues)
    )

    return (
        eigenvectors
        @
        diagonal
        @
        eigenvectors.T
    )


# ============================================================
# COST PHASE
# ============================================================

def apply_route_cost_phase(
    state,
    normalized_costs,
    gamma
):

    phase = np.exp(
        -1j *
        gamma *
        normalized_costs
    )

    return state * phase


# ============================================================
# MIXER APPLICATION
# ============================================================

def apply_route_mixer(
    state,
    mixer_matrix,
    beta
):

    if mixer_matrix.shape[0] <= 1:

        return state.copy()

    generator = (
        -1j *
        beta *
        mixer_matrix
    )

    unitary = matrix_exponential(
        generator
    )

    return unitary @ state


# ============================================================
# INITIAL STATE
# ============================================================

def initial_uniform_state(
    number_of_routes
):

    if number_of_routes <= 0:

        return np.array(
            [],
            dtype=np.complex128
        )

    return (
        np.ones(
            number_of_routes,
            dtype=np.complex128
        )
        /
        math.sqrt(
            number_of_routes
        )
    )


# ============================================================
# QAOA STATE
# ============================================================

def run_qaoa_state(
    normalized_costs,
    mixer_matrix,
    beta,
    gamma
):

    state = initial_uniform_state(
        len(normalized_costs)
    )

    state = apply_route_cost_phase(
        state,
        normalized_costs,
        gamma
    )

    state = apply_route_mixer(
        state,
        mixer_matrix,
        beta
    )

    norm = np.linalg.norm(
        state
    )

    if norm > 0:

        state = state / norm

    return state


# ============================================================
# EXPECTATION
# ============================================================

def expectation_value(
    state,
    normalized_costs
):

    probabilities = (
        np.abs(state) ** 2
    )

    return float(
        np.sum(
            probabilities *
            normalized_costs
        )
    )


# ============================================================
# QAOA PARAMETER SEARCH
# ============================================================

def optimize_qaoa_parameters(
    normalized_costs,
    mixer_matrix
):

    best_beta = 0.0
    best_gamma = 0.0

    best_expectation = float(
        "inf"
    )

    betas = np.linspace(
        0.0,
        math.pi,
        BETA_STEPS
    )

    gammas = np.linspace(
        0.0,
        math.pi,
        GAMMA_STEPS
    )

    for beta in betas:

        for gamma in gammas:

            state = run_qaoa_state(
                normalized_costs,
                mixer_matrix,
                beta,
                gamma
            )

            expectation = expectation_value(
                state,
                normalized_costs
            )

            if (
                expectation
                <
                best_expectation
            ):

                best_expectation = (
                    expectation
                )

                best_beta = beta
                best_gamma = gamma

    return (
        best_beta,
        best_gamma,
        best_expectation
    )


# ============================================================
# ROUTE PROBABILITIES
# ============================================================

def get_route_probabilities(
    state,
    routes
):

    probabilities = (
        np.abs(state) ** 2
    )

    results = []

    for index, route in enumerate(
        routes
    ):

        results.append({

            "index":
                index,

            "route":
                route,

            "probability":
                float(
                    probabilities[index]
                )
        })

    results.sort(

        key=lambda item:
        item["probability"],

        reverse=True
    )

    return results


# ============================================================
# QUANTUM MEASUREMENT
# ============================================================

def sample_quantum_routes(
    state,
    routes,
    shots=1000
):

    probabilities = (
        np.abs(state) ** 2
    )

    total_probability = np.sum(
        probabilities
    )

    if total_probability <= 0:
        return []

    probabilities = (
        probabilities /
        total_probability
    )

    samples = np.random.choice(

        len(routes),

        size=shots,

        p=probabilities
    )

    counts = {}

    for index in samples:

        index = int(index)

        counts[index] = (
            counts.get(index, 0)
            + 1
        )

    measured_routes = []

    for index, count in counts.items():

        measured_routes.append({

            "index":
                index,

            "route":
                routes[index],

            "count":
                count,

            "measured_probability":
                float(
                    count / shots
                ),

            "qaoa_probability":
                float(
                    probabilities[index]
                )
        })

    measured_routes.sort(

        key=lambda item:
        item["count"],

        reverse=True
    )

    return measured_routes


# ============================================================
# QUANTUM ROUTE SELECTION
# ============================================================

def select_quantum_route(
    state,
    routes,
    distance_matrix,
    shots=1000
):
    """
    Generate candidates through actual QAOA measurement.

    Then choose the lowest-objective route among the
    routes that were actually measured.

    This keeps the quantum probability distribution
    genuine while avoiding a poor randomly measured route.
    """

    if not routes:

        return (
            None,
            0.0,
            None,
            []
        )

    probabilities = (
        np.abs(state) ** 2
    )

    total_probability = np.sum(
        probabilities
    )

    if total_probability <= 0:

        return (
            None,
            0.0,
            None,
            []
        )

    probabilities = (
        probabilities /
        total_probability
    )

    # --------------------------------------------------------
    # ACTUAL QUANTUM SAMPLING
    # --------------------------------------------------------

    measured_routes = sample_quantum_routes(
        state,
        routes,
        shots
    )

    if not measured_routes:

        return (
            None,
            0.0,
            None,
            []
        )

    # --------------------------------------------------------
    # EVALUATE ONLY MEASURED ROUTES
    # --------------------------------------------------------

    evaluated = evaluate_routes(
        routes,
        distance_matrix
    )

    evaluated_by_index = {

        index: item

        for index, item
        in enumerate(evaluated)
    }

    measured_candidates = []

    for item in measured_routes:

        index = int(
            item["index"]
        )

        if index not in evaluated_by_index:
            continue

        candidate = evaluated_by_index[
            index
        ]

        measured_candidates.append({

            "index":
                index,

            "route":
                candidate["route"],

            "metrics":
                candidate["metrics"],

            "objective":
                candidate["objective"],

            "count":
                item["count"],

            "qaoa_probability":
                probabilities[index],

            "measured_probability":
                item[
                    "measured_probability"
                ]
        })

    if not measured_candidates:

        return (
            None,
            0.0,
            None,
            []
        )

    # --------------------------------------------------------
    # BEST ROUTE AMONG ACTUALLY MEASURED STATES
    # --------------------------------------------------------

    selected = min(

        measured_candidates,

        key=lambda item:
        item["objective"]
    )

    selected_index = int(
        selected["index"]
    )

    selected_route = selected[
        "route"
    ]

    selected_probability = float(
        probabilities[
            selected_index
        ]
    )

    return (

        selected_route,

        selected_probability,

        selected_index,

        measured_routes
    )


# ============================================================
# SMALL QAOA
# ============================================================

def run_small_qaoa(
    locations,
    deliveries=None,
    vehicle_capacity=None,
    depot_id="DEPOT"
):

    if not locations:

        return {

            "success":
                False,

            "error":
                "No locations supplied."
        }

    # --------------------------------------------------------
    # FIND DEPOT
    # --------------------------------------------------------

    depot_index = None

    for index, location in enumerate(
        locations
    ):

        if (
            location.get("id")
            ==
            depot_id
        ):

            depot_index = index
            break

    if depot_index is None:

        return {

            "success":
                False,

            "error":
                "DEPOT location not found."
        }

    # --------------------------------------------------------
    # MOVE DEPOT TO INDEX 0
    # --------------------------------------------------------

    if depot_index != 0:

        locations = (

            [locations[depot_index]]

            +

            [
                location

                for index, location
                in enumerate(locations)

                if index != depot_index
            ]
        )

    # --------------------------------------------------------
    # CAPACITY
    # --------------------------------------------------------

    total_demand = 0.0

    if deliveries is not None:

        for delivery in deliveries:

            total_demand += float(

                delivery.get(
                    "demand",
                    0
                )
            )

    if (
        vehicle_capacity is not None
        and
        total_demand >
        float(vehicle_capacity)
    ):

        return {

            "success":
                False,

            "error":
                "Vehicle capacity exceeded.",

            "total_demand":
                total_demand,

            "vehicle_capacity":
                vehicle_capacity
        }

    # --------------------------------------------------------
    # DISTANCE MATRIX
    # --------------------------------------------------------

    distance_matrix = build_distance_matrix(
        locations
    )

    # --------------------------------------------------------
    # ROUTES
    # --------------------------------------------------------

    routes = generate_valid_routes(
        len(locations),
        depot_index=0
    )

    if not routes:

        return {

            "success":
                False,

            "error":
                "No valid routes found."
        }

    # --------------------------------------------------------
    # QUANTUM COST
    # --------------------------------------------------------

    route_costs = build_route_costs(
        routes,
        distance_matrix
    )

    normalized_costs = normalize_costs(
        route_costs
    )

    # --------------------------------------------------------
    # MIXER
    # --------------------------------------------------------

    mixer_matrix = build_mixer_matrix(
        routes
    )

    # --------------------------------------------------------
    # QAOA PARAMETERS
    # --------------------------------------------------------

    (
        beta,
        gamma,
        expected_energy

    ) = optimize_qaoa_parameters(

        normalized_costs,
        mixer_matrix
    )

    # --------------------------------------------------------
    # FINAL STATE
    # --------------------------------------------------------

    state = run_qaoa_state(

        normalized_costs,
        mixer_matrix,
        beta,
        gamma
    )

    # --------------------------------------------------------
    # MEASUREMENT
    # --------------------------------------------------------

    (
        quantum_route,
        probability,
        selected_index,
        measured_routes

    ) = select_quantum_route(

        state,
        routes,
        distance_matrix,
        QAOA_SHOTS
    )

    if quantum_route is None:

        return {

            "success":
                False,

            "error":
                "QAOA measurement failed."
        }

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    if not is_valid_route(

        quantum_route,

        len(locations),

        depot_index=0
    ):

        return {

            "success":
                False,

            "error":
                "Internal QAOA route validation failed."
        }

    # --------------------------------------------------------
    # QUANTUM METRICS
    # --------------------------------------------------------

    metrics = calculate_route_metrics(

        quantum_route,

        distance_matrix
    )

    # --------------------------------------------------------
    # OBJECTIVE
    # --------------------------------------------------------

    evaluated_routes = evaluate_routes(

        routes,
        distance_matrix
    )

    objective = None

    for item in evaluated_routes:

        if item["route"] == quantum_route:

            objective = item["objective"]
            break

    if objective is None:
        objective = 0.0

    # --------------------------------------------------------
    # PROBABILITIES
    # --------------------------------------------------------

    route_probabilities = (
        get_route_probabilities(
            state,
            routes
        )
    )

    # --------------------------------------------------------
    # ROUTE NAMES
    # --------------------------------------------------------

    quantum_route_names = [

        locations[index]["id"]

        for index in quantum_route
    ]

    # --------------------------------------------------------
    # QUBITS
    # --------------------------------------------------------

    qubits = (
        len(locations)
        *
        len(locations)
    )

    # --------------------------------------------------------
    # MEASURED ROUTES
    # --------------------------------------------------------

    measured_route_output = []

    for item in measured_routes:

        measured_route_output.append({

            "route": [

                locations[index]["id"]

                for index in item["route"]
            ],

            "count":
                item["count"],

            "measured_probability":
                round(
                    item["measured_probability"],
                    4
                ),

            "qaoa_probability":
                round(
                    item["qaoa_probability"],
                    8
                )
        })

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "success":
            True,

        "route":
            quantum_route_names,

        "distance":
            metrics["distance"],

        "time":
            metrics["time"],

        "time_hours":
            metrics["time_hours"],

        "fuel":
            metrics["fuel"],

        "fuel_litres":
            metrics["fuel_litres"],

        "fuel_cost":
            metrics["fuel_cost"],

        "operational_cost":
            metrics["operational_cost"],

        "cost":
            metrics["cost"],

        "objective":
            round(
                objective,
                6
            ),

        "probability":
            round(
                probability,
                8
            ),

        "probability_percent":
            round(
                probability * 100,
                4
            ),

        "selected_route_index":
            selected_index,

        "number_of_feasible_routes":
            len(routes),

        "qubits":
            qubits,

        "shots":
            QAOA_SHOTS,

        "beta":
            round(
                beta,
                6
            ),

        "gamma":
            round(
                gamma,
                6
            ),

        "expected_energy":
            round(
                expected_energy,
                6
            ),

        "total_demand":
            total_demand,

        "route_probabilities": [

            {

                "route": [

                    locations[index]["id"]

                    for index in item["route"]
                ],

                "probability":
                    round(
                        item["probability"],
                        8
                    ),

                "probability_percent":
                    round(
                        item["probability"]
                        * 100,
                        4
                    )
            }

            for item in route_probabilities
        ],

        "measured_routes":
            measured_route_output,

        "method": (
            "QAOA p=1 "
            "Multi-Objective "
            "Feasible-Route "
            "State-Vector Simulation "
            "+ Measurement-Based Decoding"
        ),

        "message": (
            "QAOA optimization completed. "
            "Routes were generated from the "
            "quantum probability distribution, "
            "and the best measured feasible route "
            "was selected."
        )
    }


# ============================================================
# QUANTUM-INSPIRED FALLBACK
# ============================================================

def run_quantum_inspired(
    locations,
    deliveries=None,
    vehicle_capacity=None,
    depot_id="DEPOT"
):

    if not locations:

        return {

            "success":
                False,

            "error":
                "No locations supplied."
        }

    depot_index = None

    for index, location in enumerate(
        locations
    ):

        if (
            location.get("id")
            ==
            depot_id
        ):

            depot_index = index
            break

    if depot_index is None:

        return {

            "success":
                False,

            "error":
                "DEPOT location not found."
        }

    if depot_index != 0:

        locations = (

            [locations[depot_index]]

            +

            [
                location

                for index, location
                in enumerate(locations)

                if index != depot_index
            ]
        )

    total_demand = 0.0

    if deliveries is not None:

        total_demand = sum(

            float(
                delivery.get(
                    "demand",
                    0
                )
            )

            for delivery in deliveries
        )

    if (
        vehicle_capacity is not None
        and
        total_demand >
        float(vehicle_capacity)
    ):

        return {

            "success":
                False,

            "error":
                "Vehicle capacity exceeded.",

            "total_demand":
                total_demand,

            "vehicle_capacity":
                vehicle_capacity
        }

    distance_matrix = build_distance_matrix(
        locations
    )

    routes = generate_valid_routes(
        len(locations),
        depot_index=0
    )

    if not routes:

        return {

            "success":
                False,

            "error":
                "No valid routes found."
        }

    evaluated = evaluate_routes(
        routes,
        distance_matrix
    )

    best = select_best_feasible_route(
        evaluated
    )

    route = best["route"]

    metrics = best["metrics"]

    route_names = [

        locations[index]["id"]

        for index in route
    ]

    return {

        "success":
            True,

        "route":
            route_names,

        "distance":
            metrics["distance"],

        "time":
            metrics["time"],

        "time_hours":
            metrics["time_hours"],

        "fuel":
            metrics["fuel"],

        "fuel_litres":
            metrics["fuel_litres"],

        "fuel_cost":
            metrics["fuel_cost"],

        "operational_cost":
            metrics["operational_cost"],

        "cost":
            metrics["cost"],

        "objective":
            round(
                best["objective"],
                6
            ),

        "probability":
            1.0,

        "probability_percent":
            100.0,

        "qubits":
            0,

        "shots":
            0,

        "beta":
            0.0,

        "gamma":
            0.0,

        "total_demand":
            total_demand,

        "method":
            "Quantum-Inspired "
            "Optimization Fallback",

        "message":
            "Problem size exceeds the "
            "feasible-route QAOA simulation "
            "limit. Quantum-inspired fallback "
            "was used."
    }


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def run_qaoa(
    locations,
    deliveries=None,
    vehicle_capacity=None,
    depot_id="DEPOT"
):

    if not locations:

        return {

            "success":
                False,

            "error":
                "No locations supplied."
        }

    number_of_locations = len(
        locations
    )

    if number_of_locations <= 5:

        return run_small_qaoa(

            locations=locations,

            deliveries=deliveries,

            vehicle_capacity=
                vehicle_capacity,

            depot_id=depot_id
        )

    return run_quantum_inspired(

        locations=locations,

        deliveries=deliveries,

        vehicle_capacity=
            vehicle_capacity,

        depot_id=depot_id
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("        QUANTUMROUTE QAOA TEST")
    print("=" * 60)
    print()

    locations = [

        {
            "id":
                "DEPOT",

            "x":
                0.0,

            "y":
                0.0,

            "lat":
                16.5115306,

            "lon":
                80.6160469
        },

        {
            "id":
                "D001",

            "x":
                100.0,

            "y":
                50.0,

            "lat":
                14.449918,

            "lon":
                79.986967
        },

        {
            "id":
                "D002",

            "x":
                250.0,

            "y":
                180.0,

            "lat":
                16.713114,

            "lon":
                81.104365
        },

        {
            "id":
                "D003",

            "x":
                -80.0,

            "y":
                120.0,

            "lat":
                16.299737,

            "lon":
                80.457293
        }
    ]

    deliveries = [

        {
            "id":
                "D001",

            "demand":
                20
        },

        {
            "id":
                "D002",

            "demand":
                15
        },

        {
            "id":
                "D003",

            "demand":
                17
        }
    ]

    result = run_qaoa(

        locations=locations,

        deliveries=deliveries,

        vehicle_capacity=100,

        depot_id="DEPOT"
    )

    print()

    print(
        "Success              :",
        result.get("success")
    )

    print(
        "Error                :",
        result.get("error")
    )

    print(
        "Route                :",
        result.get("route")
    )

    print(
        "Distance             :",
        result.get("distance"),
        "km"
    )

    print(
        "Time                 :",
        result.get("time"),
        "hours"
    )

    print(
        "Fuel                 :",
        result.get("fuel"),
        "litres"
    )

    print(
        "Cost                 :",
        result.get("cost"),
        "INR"
    )

    print(
        "Objective            :",
        result.get("objective")
    )

    print(
        "Probability          :",
        result.get("probability")
    )

    print(
        "Probability (%)      :",
        result.get("probability_percent")
    )

    print(
        "Qubits               :",
        result.get("qubits")
    )

    print(
        "Shots                :",
        result.get("shots")
    )

    print(
        "Beta                 :",
        result.get("beta")
    )

    print(
        "Gamma                :",
        result.get("gamma")
    )

    print(
        "Expected Energy      :",
        result.get("expected_energy")
    )

    print(
        "Feasible Routes      :",
        result.get(
            "number_of_feasible_routes"
        )
    )

    print(
        "Method               :",
        result.get("method")
    )

    print()

    print("=" * 60)

    if result.get("success"):

        print()
        print("QAOA ROUTE PROBABILITIES")
        print("-" * 60)

        for item in result.get(
            "route_probabilities",
            []
        ):

            print(
                item["route"],
                "->",
                item["probability_percent"],
                "%"
            )

        print()
        print("MEASURED ROUTES")
        print("-" * 60)

        for item in result.get(
            "measured_routes",
            []
        ):

            print(
                item["route"],
                "->",
                "shots:",
                item["count"],
                "| QAOA:",
                item["qaoa_probability"],
                "| measured:",
                item["measured_probability"]
            )

    print()