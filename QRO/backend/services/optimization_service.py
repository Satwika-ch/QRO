"""
Optimization service for QuantumRoute.

Connects:
    Data
      ↓
    Algorithms
      ↓
    Classical + Quantum optimization
      ↓
    Comparison
"""

from algorithms.classical_optimizer import (
    optimize_classical
)

from algorithms.qaoa_optimizer import (
    run_qaoa
)

from .route_service import (
    get_locations,
    get_deliveries
)

from .vehicle_service import (
    get_vehicle_by_id
)


def optimize_route(
    vehicle_id="V001",
    depot_id="DEPOT"
):
    """
    Run both classical and quantum
    route optimization.
    """

    # -----------------------------
    # Load data
    # -----------------------------

    locations = get_locations()

    deliveries = get_deliveries()

    # -----------------------------
    # Get vehicle
    # -----------------------------

    vehicle = get_vehicle_by_id(
        vehicle_id
    )

    if vehicle is None:

        return {
            "success": False,
            "message": "Vehicle not found."
        }

    vehicle_capacity = (
        vehicle["capacity"]
    )

    # -----------------------------
    # Classical optimization
    # -----------------------------

    classical_result = (
        optimize_classical(
            locations=locations,
            deliveries=deliveries,
            vehicle_capacity=vehicle_capacity,
            depot_id=depot_id
        )
    )

    # -----------------------------
    # Quantum optimization
    # -----------------------------

    # The QAOA prototype works with
    # a small number of locations.

    quantum_result = run_qaoa(
        locations=locations
    )

    # -----------------------------
    # Compare
    # -----------------------------

    comparison = None

    if (
        classical_result.get("success")
        and quantum_result.get("success")
    ):

        classical_distance = (
            classical_result["distance"]
        )

        quantum_distance = (
            quantum_result["distance"]
        )

        improvement = 0.0

        if classical_distance > 0:

            improvement = (
                (
                    classical_distance
                    - quantum_distance
                )
                / classical_distance
            ) * 100

        comparison = {
            "classical_distance": round(
                classical_distance,
                2
            ),
            "quantum_distance": round(
                quantum_distance,
                2
            ),
            "distance_difference": round(
                classical_distance
                - quantum_distance,
                2
            ),
            "percentage_difference": round(
                improvement,
                2
            )
        }

    return {
        "success": True,

        "vehicle": vehicle,

        "classical": classical_result,

        "quantum": quantum_result,

        "comparison": comparison
    }