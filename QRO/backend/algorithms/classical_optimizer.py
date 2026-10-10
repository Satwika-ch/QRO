"""
Classical route optimizer.

For the hackathon prototype we use exhaustive permutation
search for small delivery sets.

This gives us a reliable classical baseline that we can
compare against the quantum QAOA approach.
"""

from itertools import permutations

from .route_constraints import (
    calculate_route_distance,
    calculate_total_demand,
    validate_route,
    calculate_route_cost
)


def optimize_classical(
    locations,
    deliveries,
    vehicle_capacity,
    depot_id="DEPOT"
):
    """
    Find the best feasible route using classical
    exhaustive search.

    The depot is added internally if it is not already
    present in the locations list.
    """

    # -------------------------------------------------
    # FIX: Make sure DEPOT exists in the location list
    # -------------------------------------------------

    normalized_locations = list(locations)

    depot_exists = any(
        location.get("id") == depot_id
        for location in normalized_locations
    )

    if not depot_exists:
        normalized_locations.insert(
            0,
            {
                "id": depot_id,
                "x": 0,
                "y": 0
            }
        )

    # -------------------------------------------------
    # Get delivery locations
    # -------------------------------------------------

    delivery_locations = [
        delivery["location_id"]
        for delivery in deliveries
    ]

    # -------------------------------------------------
    # Check that every delivery location exists
    # -------------------------------------------------

    available_location_ids = {
        location["id"]
        for location in normalized_locations
    }

    for location_id in delivery_locations:
        if location_id not in available_location_ids:
            return {
                "success": False,
                "message": f"Location '{location_id}' not found."
            }

    # -------------------------------------------------
    # Check total demand
    # -------------------------------------------------

    total_demand = calculate_total_demand(
        delivery_locations,
        deliveries
    )

    if total_demand > vehicle_capacity:
        return {
            "success": False,
            "message": (
                f"Total demand ({total_demand}) exceeds "
                f"vehicle capacity ({vehicle_capacity})."
            ),
            "total_demand": total_demand
        }

    # -------------------------------------------------
    # Exhaustive search
    # -------------------------------------------------

    best_route = None
    best_distance = float("inf")
    best_cost = float("inf")

    checked_routes = 0
    feasible_routes = 0

    for permutation in permutations(delivery_locations):

        route = [
            depot_id,
            *permutation,
            depot_id
        ]

        checked_routes += 1

        validation = validate_route(
            route=route,
            locations=normalized_locations,
            deliveries=deliveries,
            vehicle_capacity=vehicle_capacity
        )

        if not validation["valid"]:
            continue

        feasible_routes += 1

        distance = calculate_route_distance(
            route,
            normalized_locations
        )

        cost = calculate_route_cost(
            distance
        )

        if distance < best_distance:
            best_route = route
            best_distance = distance
            best_cost = cost

    # -------------------------------------------------
    # No route found
    # -------------------------------------------------

    if best_route is None:
        return {
            "success": False,
            "message": "No feasible route found.",
            "checked_routes": checked_routes,
            "feasible_routes": feasible_routes,
            "total_demand": total_demand
        }

    # -------------------------------------------------
    # Final result
    # -------------------------------------------------

    return {
        "success": True,
        "method": "Classical Exhaustive Search",
        "route": best_route,
        "distance": round(best_distance, 2),
        "cost": round(best_cost, 2),
        "total_demand": total_demand,
        "checked_routes": checked_routes,
        "feasible_routes": feasible_routes
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    locations = [
        {
            "id": "A",
            "x": 2,
            "y": 3
        },
        {
            "id": "B",
            "x": 5,
            "y": 4
        },
        {
            "id": "C",
            "x": 6,
            "y": 1
        }
    ]

    deliveries = [
        {
            "id": "D1",
            "location_id": "A",
            "demand": 10
        },
        {
            "id": "D2",
            "location_id": "B",
            "demand": 15
        },
        {
            "id": "D3",
            "location_id": "C",
            "demand": 20
        }
    ]

    result = optimize_classical(
        locations=locations,
        deliveries=deliveries,
        vehicle_capacity=50,
        depot_id="DEPOT"
    )

    print("\n========== CLASSICAL OPTIMIZER ==========")

    if result["success"]:

        print("Method:", result["method"])
        print("Best Route:", " -> ".join(result["route"]))
        print("Distance:", result["distance"])
        print("Cost:", result["cost"])
        print("Total Demand:", result["total_demand"])
        print("Routes Checked:", result["checked_routes"])
        print("Feasible Routes:", result["feasible_routes"])

    else:

        print(result["message"])