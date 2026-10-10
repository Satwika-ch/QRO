"""
QuantumRoute Optimization Coordinator
VNQFF-08: Quantum-Enhanced Last-Mile Route Optimisation

Compares:
    Classical User-Order Baseline
    QAOA / Quantum-Inspired Optimized Route
    Exact Classical Benchmark (validation only)

All routes in one optimization request use the same distance matrix.
"""

import math

from algorithms.qaoa_optimizer import (
    run_qaoa,
    build_distance_matrix,
    calculate_route_metrics,
    generate_valid_routes,
    select_best_feasible_route,
    evaluate_routes,
)


def route_names_to_indexes(route_names, locations):
    """Convert route IDs into location indexes."""
    if not route_names:
        return []

    location_index = {
        location.get("id"): index
        for index, location in enumerate(locations)
    }

    route = []
    for name in route_names:
        if name not in location_index:
            return []
        route.append(location_index[name])

    return route


def add_classical_metrics(
    classical_result,
    locations,
    distance_matrix=None,
):
    """Recalculate route metrics using the supplied shared matrix."""
    if not classical_result:
        return classical_result

    route = route_names_to_indexes(
        classical_result.get("route", []),
        locations,
    )
    if not route:
        return classical_result

    if distance_matrix is None:
        distance_matrix = build_distance_matrix(locations)

    metrics = calculate_route_metrics(route, distance_matrix)
    classical_result.update(metrics)
    return classical_result


def build_classical_baseline(
    locations,
    distance_matrix=None,
):
    """
    Visit deliveries in the exact order entered by the user:
    DEPOT -> D001 -> D002 -> ... -> DEPOT.
    """
    if not locations:
        return {
            "success": False,
            "error": "Locations are required.",
        }

    if len(locations) < 2:
        return {
            "success": False,
            "error": "At least one delivery is required.",
        }

    if locations[0].get("id") != "DEPOT":
        return {
            "success": False,
            "error": "DEPOT must be the first location.",
        }

    if distance_matrix is None:
        distance_matrix = build_distance_matrix(locations)

    route = list(range(len(locations)))
    route.append(0)

    metrics = calculate_route_metrics(route, distance_matrix)
    route_names = [locations[index]["id"] for index in route]

    return {
        "success": True,
        "route": route_names,
        **metrics,
        "method": "Classical User-Order Baseline",
        "message": (
            "Classical baseline follows the delivery order "
            "entered by the user."
        ),
    }


def build_exact_classical_benchmark(
    locations,
    distance_matrix=None,
):
    """Calculate the best enumerated classical route for validation."""
    if not locations:
        return {
            "success": False,
            "error": "Locations are required.",
        }

    if distance_matrix is None:
        distance_matrix = build_distance_matrix(locations)

    routes = generate_valid_routes(
        len(locations),
        depot_index=0,
    )

    if not routes:
        return {
            "success": False,
            "error": "No valid classical routes.",
        }

    evaluated = evaluate_routes(routes, distance_matrix)
    best = select_best_feasible_route(evaluated)

    if best is None:
        return {
            "success": False,
            "error": "Unable to select the best classical route.",
        }

    route = best["route"]
    metrics = best["metrics"]

    return {
        "success": True,
        "route": [locations[index]["id"] for index in route],
        **metrics,
        "objective": best["objective"],
        "method": "Classical Exact Benchmark",
    }


def _number(value, field_name):
    """Convert a metric to a finite float or raise a clear error."""
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be a finite number.")
    return result


def _make_comparison(classical_result, quantum_result):
    """Create the comparison from the two actual route metrics."""
    metric_pairs = {
        "distance": ("distance", "distance"),
        "time": ("time", "time"),
        "fuel": ("fuel", "fuel"),
        "cost": ("cost", "cost"),
    }

    comparison = {}

    for metric_name, (classical_key, quantum_key) in metric_pairs.items():
        classical_value = _number(
            classical_result[classical_key],
            f"classical {metric_name}",
        )
        quantum_value = _number(
            quantum_result[quantum_key],
            f"quantum {metric_name}",
        )

        difference = classical_value - quantum_value
        improvement = (
            difference / classical_value * 100.0
            if classical_value > 0
            else 0.0
        )

        comparison[f"classical_{metric_name}"] = round(
            classical_value, 2
        )
        comparison[f"quantum_{metric_name}"] = round(
            quantum_value, 2
        )
        comparison[f"{metric_name}_difference"] = round(
            difference, 2
        )

        # Existing frontend field names retained.
        if metric_name == "distance":
            comparison["distance_saved"] = round(difference, 2)
            comparison["distance_improvement"] = round(improvement, 2)
        elif metric_name == "time":
            comparison["time_saved"] = round(difference, 2)
            comparison["time_improvement"] = round(improvement, 2)
        elif metric_name == "fuel":
            comparison["fuel_saved"] = round(difference, 2)
            comparison["fuel_improvement"] = round(improvement, 2)
        elif metric_name == "cost":
            comparison["cost_saved"] = round(difference, 2)
            comparison["cost_improvement"] = round(improvement, 2)

    return comparison


def run_optimization(
    locations,
    deliveries,
    vehicle_capacity,
    depot_id="DEPOT",
):
    """Run the baseline, validation benchmark, and QAOA optimizer."""
    if not locations:
        return {
            "success": False,
            "error": "Locations are required.",
        }

    if not deliveries:
        return {
            "success": False,
            "error": "Deliveries are required.",
        }

    if vehicle_capacity is None:
        return {
            "success": False,
            "error": "Vehicle capacity is required.",
        }

    try:
        vehicle_capacity = _number(
            vehicle_capacity,
            "Vehicle capacity",
        )
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Vehicle capacity must be a valid number.",
        }

    if vehicle_capacity <= 0:
        return {
            "success": False,
            "error": "Vehicle capacity must be greater than zero.",
        }

    if locations[0].get("id") != depot_id:
        return {
            "success": False,
            "error": f"The first location must be {depot_id}.",
        }

    location_ids = [item.get("id") for item in locations]
    if len(set(location_ids)) != len(location_ids):
        return {
            "success": False,
            "error": "Each location must have a unique id.",
        }

    try:
        total_demand = sum(
            _number(delivery.get("demand", 0), "Delivery demand")
            for delivery in deliveries
        )
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Invalid delivery demand.",
        }

    if total_demand < 0:
        return {
            "success": False,
            "error": "Delivery demand cannot be negative.",
        }

    if total_demand > vehicle_capacity:
        return {
            "success": False,
            "error": "Vehicle capacity exceeded.",
            "total_demand": round(total_demand, 2),
            "vehicle_capacity": round(vehicle_capacity, 2),
        }

    # Build the distance matrix ONCE for this optimization request.
    try:
        distance_matrix = build_distance_matrix(locations)
    except Exception as error:
        return {
            "success": False,
            "error": f"Unable to build distance matrix: {error}",
        }

    try:
        classical_result = build_classical_baseline(
            locations,
            distance_matrix=distance_matrix,
        )
        if not classical_result.get("success"):
            return classical_result
    except Exception as error:
        return {
            "success": False,
            "error": f"Classical baseline failed: {error}",
        }

    try:
        exact_classical = build_exact_classical_benchmark(
            locations,
            distance_matrix=distance_matrix,
        )
    except Exception as error:
        exact_classical = {
            "success": False,
            "error": str(error),
        }

    try:
        quantum_result = run_qaoa(
            locations=locations,
            deliveries=deliveries,
            vehicle_capacity=vehicle_capacity,
            depot_id=depot_id,
            distance_matrix=distance_matrix,
        )
    except Exception as error:
        quantum_result = {
            "success": False,
            "message": f"Quantum optimization failed: {error}",
            "error": str(error),
            "route": [],
            "distance": None,
            "time": None,
            "fuel": None,
            "cost": None,
            "probability": None,
            "qubits": None,
            "method": "QAOA",
        }

    comparison = None

    if quantum_result.get("success"):
        try:
            comparison = _make_comparison(
                classical_result,
                quantum_result,
            )
        except (KeyError, TypeError, ValueError) as error:
            return {
                "success": False,
                "error": f"Unable to compare route metrics: {error}",
                "classical": classical_result,
                "quantum": quantum_result,
                "exact_classical": exact_classical,
            }

    return {
        "success": True,
        "classical": classical_result,
        "quantum": quantum_result,
        "comparison": comparison,
        "exact_classical": exact_classical,
        "total_demand": round(total_demand, 2),
        "vehicle_capacity": round(vehicle_capacity, 2),
        "depot_id": depot_id,
        "optimization_summary": {
            "baseline": "Classical User-Order Baseline",
            "optimized": quantum_result.get(
                "method", "QAOA Optimization"
            ),
            "validation": "Exact Classical Benchmark",
            "goal": "Minimize distance, time, fuel and cost",
        },
    }
def run_multi_vehicle_optimization(
    locations,
    deliveries,
    vehicles,
    depot_id="DEPOT",
):
    """
    Assign deliveries to multiple vehicles based on capacity,
    then create a separate nearest-neighbour route for each vehicle.

    This is a classical capacity-based assignment heuristic.
    It does not replace the existing QAOA optimizer.
    """

    if not locations or not deliveries or not vehicles:
        return {
            "success": False,
            "error": "Locations, deliveries, and vehicles are required.",
        }

    location_index = {
        loc["id"]: index
        for index, loc in enumerate(locations)
    }

    if depot_id not in location_index:
        return {
            "success": False,
            "error": f"Depot {depot_id} was not found.",
        }

    if len(location_index) != len(locations):
        return {
            "success": False,
            "error": "Location IDs must be unique.",
        }

    try:
        distance_matrix = build_distance_matrix(locations)

        fleet = []
        for vehicle in vehicles:
            capacity = _number(
                vehicle.get("capacity"),
                f'{vehicle.get("id")} capacity',
            )

            if capacity <= 0:
                raise ValueError("Vehicle capacity must be positive.")

            fleet.append({
                **vehicle,
                "capacity": capacity,
                "remaining": capacity,
                "assigned": [],
            })

        pending = []

        for delivery in deliveries:
            demand = _number(
                delivery.get("demand", 0),
                "Delivery demand",
            )

            if demand < 0:
                raise ValueError("Delivery demand cannot be negative.")

            location_id = delivery.get(
                "location_id",
                delivery.get("id"),
            )

            if location_id not in location_index:
                raise ValueError(
                    f"Location {location_id} was not found."
                )

            if demand > max(v["capacity"] for v in fleet):
                raise ValueError(
                    f"Delivery {delivery.get('id')} exceeds "
                    "the capacity of every vehicle."
                )

            pending.append({
                **delivery,
                "location_id": location_id,
                "demand": demand,
            })

        total_demand = sum(d["demand"] for d in pending)
        total_capacity = sum(v["capacity"] for v in fleet)

        if total_demand > total_capacity:
            return {
                "success": False,
                "error": "Total delivery demand exceeds fleet capacity.",
                "total_demand": round(total_demand, 2),
                "total_capacity": round(total_capacity, 2),
            }

        # Assign larger deliveries first, using the tightest
        # vehicle capacity that can accommodate each delivery.
        pending.sort(key=lambda d: d["demand"], reverse=True)

        for delivery in pending:
            candidates = [
                v for v in fleet
                if v["remaining"] >= delivery["demand"]
            ]

            if not candidates:
                return {
                    "success": False,
                    "error": (
                        f"Unable to assign delivery "
                        f"{delivery.get('id')} within vehicle capacities."
                    ),
                }

            vehicle = min(
                candidates,
                key=lambda v: v["remaining"] - delivery["demand"],
            )

            vehicle["assigned"].append(delivery)
            vehicle["remaining"] -= delivery["demand"]

        # Build a separate nearest-neighbour route for each vehicle.
        results = []

        for vehicle in fleet:
            current = location_index[depot_id]
            remaining_deliveries = vehicle["assigned"][:]
            route_ids = [depot_id]
            route_indexes = [current]

            while remaining_deliveries:
                next_delivery = min(
                    remaining_deliveries,
                    key=lambda d: distance_matrix[
                        current
                    ][location_index[d["location_id"]]],
                )

                next_index = location_index[
                    next_delivery["location_id"]
                ]

                route_indexes.append(next_index)
                route_ids.append(next_delivery["location_id"])
                current = next_index
                remaining_deliveries.remove(next_delivery)

            # Return to depot.
            route_indexes.append(location_index[depot_id])
            route_ids.append(depot_id)

            metrics = calculate_route_metrics(
                route_indexes,
                distance_matrix,
            )

            results.append({
                "id": vehicle["id"],
                "name": vehicle.get("name", vehicle["id"]),
                "capacity": vehicle["capacity"],
                "assigned_demand": round(
                    sum(d["demand"] for d in vehicle["assigned"]), 2
                ),
                "remaining_capacity": round(vehicle["remaining"], 2),
                "available": vehicle.get("available", True),
                "status": vehicle.get("status", "active"),
                "route": route_ids,
                "delivery_ids": [
                    d.get("id") for d in vehicle["assigned"]
                ],
                **metrics,
            })

        return {
            "success": True,
            "method": "Capacity-Based Multi-Vehicle Routing",
            "total_demand": round(total_demand, 2),
            "total_capacity": round(total_capacity, 2),
            "assigned_deliveries": sum(
                len(v["delivery_ids"]) for v in results
            ),
            "vehicles": results,
        }

    except (TypeError, ValueError, KeyError, IndexError) as error:
        return {
            "success": False,
            "error": str(error),
        }

if __name__ == "__main__":
    print("=" * 60)
    print("QUANTUMROUTE OPTIMIZATION COORDINATOR")
    print("Classical baseline | Exact benchmark | QAOA")
    print("Metrics: Distance / Time / Fuel / Cost")
    print("=" * 60)