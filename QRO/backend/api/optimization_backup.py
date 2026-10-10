"""
QuantumRoute Optimization Coordinator

VNQFF-08
Quantum-Enhanced Last-Mile Route Optimisation

Comparison:

    Classical Baseline Route
              VS
    QAOA Optimized Route

The exact classical optimizer is also executed internally
as a benchmark so that the quantum result can be validated.

Metrics:
    Distance
    Time
    Fuel
    Cost
"""

from algorithms.classical_optimizer import optimize_classical

from algorithms.qaoa_optimizer import (
    run_qaoa,
    build_distance_matrix,
    calculate_route_metrics,
    generate_valid_routes,
    select_best_feasible_route,
    evaluate_routes
)


# ============================================================
# ROUTE NAME -> INDEX
# ============================================================

def route_names_to_indexes(
    route_names,
    locations
):
    """
    Convert route names into location indexes.
    """

    if not route_names:
        return []

    location_index = {
        location["id"]: index
        for index, location
        in enumerate(locations)
    }

    route = []

    for name in route_names:

        if name not in location_index:
            return []

        route.append(
            location_index[name]
        )

    return route


# ============================================================
# ADD COMMON METRICS
# ============================================================

def add_classical_metrics(
    classical_result,
    locations
):
    """
    Add distance, time, fuel and cost
    using the same metric model as QAOA.
    """

    if not classical_result:
        return classical_result

    route_names = classical_result.get(
        "route",
        []
    )

    route = route_names_to_indexes(
        route_names,
        locations
    )

    if not route:
        return classical_result

    distance_matrix = (
        build_distance_matrix(
            locations
        )
    )

    metrics = calculate_route_metrics(
        route,
        distance_matrix
    )

    classical_result["distance"] = (
        metrics["distance"]
    )

    classical_result["time"] = (
        metrics["time_hours"]
    )

    classical_result["time_hours"] = (
        metrics["time_hours"]
    )

    classical_result["fuel"] = (
        metrics["fuel_litres"]
    )

    classical_result["fuel_litres"] = (
        metrics["fuel_litres"]
    )

    classical_result["cost"] = (
        metrics["cost"]
    )

    classical_result["fuel_cost"] = (
        metrics["fuel_cost"]
    )

    classical_result["operational_cost"] = (
        metrics["operational_cost"]
    )

    return classical_result


# ============================================================
# CLASSICAL BASELINE
# ============================================================

# ============================================================
# CLASSICAL BASELINE
# ============================================================
def route_distance_for_baseline(
    route,
    distance_matrix
):
    """
    Calculate route distance for the
    classical baseline.
    """

    total = 0.0

    for i in range(
        len(route) - 1
    ):

        total += distance_matrix[
            route[i],
            route[i + 1]
        ]

    return float(total)

    
def build_classical_baseline(
    locations
):
    """
    Build a strong classical baseline using:

        1. Nearest Neighbor
        2. 2-opt local improvement

    This gives a good near-optimal classical route
    instead of simply following the user's input order.

    QAOA can then be compared against this strong
    classical baseline.
    """

    if not locations:

        return {
            "success": False,
            "error": "Locations are required."
        }

    if len(locations) < 2:

        return {
            "success": False,
            "error": (
                "At least one delivery "
                "is required."
            )
        }

    # --------------------------------------------------------
    # DEPOT
    # --------------------------------------------------------

    depot_index = 0

    distance_matrix = (
        build_distance_matrix(
            locations
        )
    )

    # --------------------------------------------------------
    # STEP 1
    # NEAREST NEIGHBOR
    # --------------------------------------------------------

    unvisited = set(
        range(
            len(locations)
        )
    )

    unvisited.discard(
        depot_index
    )

    route = [
        depot_index
    ]

    current = depot_index

    while unvisited:

        nearest = min(
            unvisited,
            key=lambda index:
                distance_matrix[
                    current,
                    index
                ]
        )

        route.append(
            nearest
        )

        unvisited.remove(
            nearest
        )

        current = nearest

    # Return to depot
    route.append(
        depot_index
    )

    # --------------------------------------------------------
    # STEP 2
    # 2-OPT IMPROVEMENT
    # --------------------------------------------------------

    improved = True

    while improved:

        improved = False

        best_distance = (
            route_distance_for_baseline(
                route,
                distance_matrix
            )
        )

        # Don't modify depot positions.
        for i in range(
            1,
            len(route) - 2
        ):

            for j in range(
                i + 1,
                len(route) - 1
            ):

                candidate = (
                    route[:i]
                    +
                    route[i:j + 1][::-1]
                    +
                    route[j + 1:]
                )

                candidate_distance = (
                    route_distance_for_baseline(
                        candidate,
                        distance_matrix
                    )
                )

                if (
                    candidate_distance
                    <
                    best_distance - 1e-9
                ):

                    route = candidate

                    best_distance = (
                        candidate_distance
                    )

                    improved = True

    # --------------------------------------------------------
    # FINAL METRICS
    # --------------------------------------------------------

    metrics = calculate_route_metrics(
        route,
        distance_matrix
    )

    route_names = [
        locations[index]["id"]
        for index in route
    ]

    return {

        "success": True,

        "route": route_names,

        "distance": metrics[
            "distance"
        ],

        "time": metrics[
            "time_hours"
        ],

        "time_hours": metrics[
            "time_hours"
        ],

        "fuel": metrics[
            "fuel_litres"
        ],

        "fuel_litres": metrics[
            "fuel_litres"
        ],

        "fuel_cost": metrics[
            "fuel_cost"
        ],

        "operational_cost": metrics[
            "operational_cost"
        ],

        "cost": metrics[
            "cost"
        ],

        "method": (
            "Classical "
            "Nearest Neighbor + 2-opt"
        ),

        "message": (
            "Classical baseline generated "
            "using nearest-neighbor routing "
            "followed by 2-opt local improvement."
        )
    }

# ============================================================
# EXACT CLASSICAL BENCHMARK
# ============================================================

def build_exact_classical_benchmark(
    locations
):
    """
    Find the exact best classical route.

    This is kept internally as a validation benchmark.
    """

    routes = generate_valid_routes(
        len(locations),
        depot_index=0
    )

    if not routes:
        return {
            "success": False,
            "error": "No valid classical routes."
        }

    evaluated = evaluate_routes(
        routes,
        build_distance_matrix(locations)
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

        "success": True,

        "route": route_names,

        "distance": metrics[
            "distance"
        ],

        "time": metrics[
            "time_hours"
        ],

        "time_hours": metrics[
            "time_hours"
        ],

        "fuel": metrics[
            "fuel_litres"
        ],

        "fuel_litres": metrics[
            "fuel_litres"
        ],

        "cost": metrics[
            "cost"
        ],

        "objective": best[
            "objective"
        ],

        "method": (
            "Classical Exact "
            "Benchmark"
        )
    }


# ============================================================
# MAIN OPTIMIZATION
# ============================================================

def run_optimization(
    locations,
    deliveries,
    vehicle_capacity,
    depot_id="DEPOT"
):
    """
    Execute:

        1. Classical baseline
        2. Exact classical benchmark
        3. QAOA optimization
        4. Improvement calculation
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not locations:

        return {
            "success": False,
            "error": "Locations are required."
        }

    if not deliveries:

        return {
            "success": False,
            "error": "Deliveries are required."
        }

    if vehicle_capacity is None:

        return {
            "success": False,
            "error": (
                "Vehicle capacity is required."
            )
        }

    try:

        vehicle_capacity = float(
            vehicle_capacity
        )

    except (
        TypeError,
        ValueError
    ):

        return {
            "success": False,
            "error": (
                "Vehicle capacity "
                "must be a number."
            )
        }

    if locations[0].get("id") != depot_id:

        return {
            "success": False,
            "error": (
                f"The first location "
                f"must be {depot_id}."
            )
        }

    # --------------------------------------------------------
    # CAPACITY CHECK
    # --------------------------------------------------------

    total_demand = sum(
        float(
            delivery.get(
                "demand",
                0
            )
        )
        for delivery in deliveries
    )

    if total_demand > vehicle_capacity:

        return {
            "success": False,
            "error": (
                "Vehicle capacity exceeded."
            ),
            "total_demand": total_demand,
            "vehicle_capacity": vehicle_capacity
        }

    # --------------------------------------------------------
    # CLASSICAL BASELINE
    # --------------------------------------------------------

    try:

        classical_result = (
            build_classical_baseline(
                locations
            )
        )

    except Exception as error:

        import traceback

        traceback.print_exc()

        return {
            "success": False,
            "error": (
                "Classical baseline failed: "
                f"{str(error)}"
            )
        }

    # --------------------------------------------------------
    # EXACT CLASSICAL BENCHMARK
    # --------------------------------------------------------

    try:

        exact_classical = (
            build_exact_classical_benchmark(
                locations
            )
        )

    except Exception as error:

        import traceback

        traceback.print_exc()

        exact_classical = {
            "success": False,
            "error": str(error)
        }

    # --------------------------------------------------------
    # QUANTUM QAOA
    # --------------------------------------------------------

    try:

        quantum_result = run_qaoa(

            locations=locations,

            deliveries=deliveries,

            vehicle_capacity=vehicle_capacity,

            depot_id=depot_id

        )

    except Exception as error:

        import traceback

        traceback.print_exc()

        quantum_result = {

            "success": False,

            "message": (
                "Quantum optimization failed: "
                f"{str(error)}"
            ),

            "route": [],

            "distance": None,

            "time": None,

            "fuel": None,

            "cost": None,

            "probability": None,

            "qubits": None,

            "method": "QAOA"

        }

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    comparison = None

    if (
        classical_result.get(
            "success",
            False
        )
        and
        quantum_result.get(
            "success",
            False
        )
    ):

        classical_distance = float(
            classical_result[
                "distance"
            ]
        )

        quantum_distance = float(
            quantum_result[
                "distance"
            ]
        )

        classical_time = float(
            classical_result[
                "time"
            ]
        )

        quantum_time = float(
            quantum_result[
                "time"
            ]
        )

        classical_fuel = float(
            classical_result[
                "fuel"
            ]
        )

        quantum_fuel = float(
            quantum_result[
                "fuel"
            ]
        )

        classical_cost = float(
            classical_result[
                "cost"
            ]
        )

        quantum_cost = float(
            quantum_result[
                "cost"
            ]
        )

        # ----------------------------------------------------
        # SAVINGS
        # ----------------------------------------------------

        distance_saved = (
            classical_distance
            -
            quantum_distance
        )

        time_saved = (
            classical_time
            -
            quantum_time
        )

        fuel_saved = (
            classical_fuel
            -
            quantum_fuel
        )

        cost_saved = (
            classical_cost
            -
            quantum_cost
        )

        # ----------------------------------------------------
        # PERCENTAGES
        # ----------------------------------------------------

        distance_improvement = 0.0

        if classical_distance > 0:

            distance_improvement = (
                distance_saved
                /
                classical_distance
                *
                100.0
            )

        time_improvement = 0.0

        if classical_time > 0:

            time_improvement = (
                time_saved
                /
                classical_time
                *
                100.0
            )

        fuel_improvement = 0.0

        if classical_fuel > 0:

            fuel_improvement = (
                fuel_saved
                /
                classical_fuel
                *
                100.0
            )

        cost_improvement = 0.0

        if classical_cost > 0:

            cost_improvement = (
                cost_saved
                /
                classical_cost
                *
                100.0
            )

        comparison = {

            # ------------------------------------------------
            # DISTANCE
            # ------------------------------------------------

            "classical_distance": round(
                classical_distance,
                2
            ),

            "quantum_distance": round(
                quantum_distance,
                2
            ),

            "distance_difference": round(
                distance_saved,
                2
            ),

            "distance_saved": round(
                distance_saved,
                2
            ),

            "distance_improvement": round(
                distance_improvement,
                2
            ),

            # ------------------------------------------------
            # TIME
            # ------------------------------------------------

            "classical_time": round(
                classical_time,
                2
            ),

            "quantum_time": round(
                quantum_time,
                2
            ),

            "time_difference": round(
                time_saved,
                2
            ),

            "time_saved": round(
                time_saved,
                2
            ),

            "time_improvement": round(
                time_improvement,
                2
            ),

            # ------------------------------------------------
            # FUEL
            # ------------------------------------------------

            "classical_fuel": round(
                classical_fuel,
                2
            ),

            "quantum_fuel": round(
                quantum_fuel,
                2
            ),

            "fuel_difference": round(
                fuel_saved,
                2
            ),

            "fuel_saved": round(
                fuel_saved,
                2
            ),

            "fuel_improvement": round(
                fuel_improvement,
                2
            ),

            # ------------------------------------------------
            # COST
            # ------------------------------------------------

            "classical_cost": round(
                classical_cost,
                2
            ),

            "quantum_cost": round(
                quantum_cost,
                2
            ),

            "cost_difference": round(
                cost_saved,
                2
            ),

            "cost_saved": round(
                cost_saved,
                2
            ),

            "cost_improvement": round(
                cost_improvement,
                2
            )
        }

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        # Frontend continues to use these
        "classical": classical_result,

        "quantum": quantum_result,

        "comparison": comparison,

        # Additional validation information
        "exact_classical": exact_classical,

        "total_demand": round(
            total_demand,
            2
        ),

        "vehicle_capacity": round(
            vehicle_capacity,
            2
        ),

        "depot_id": depot_id,

        "optimization_summary": {

            "baseline": (
                "Classical user-order "
                "baseline"
            ),

            "optimized": (
                "QAOA state-vector "
                "simulation"
            ),

            "validation": (
                "Exact classical "
                "benchmark"
            ),

            "goal": (
                "Minimize distance, "
                "time, fuel and cost"
            )
        }
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(
        "   QUANTUMROUTE OPTIMIZATION COORDINATOR"
    )
    print("=" * 60)

    print()
    print(
        "Classical baseline : Loaded"
    )

    print(
        "Exact benchmark    : Loaded"
    )

    print(
        "QAOA simulator     : Loaded"
    )

    print(
        "Metrics            : "
        "Distance / Time / Fuel / Cost"
    )

    print(
        "Status             : Ready"
    )

    print("=" * 60)
    print()