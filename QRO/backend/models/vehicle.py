"""
Vehicle model for QuantumRoute.
"""


class Vehicle:
    """
    Represents a delivery vehicle.
    """

    def __init__(
        self,
        vehicle_id,
        name,
        capacity,
        fuel_cost_per_km=10,
        available=True
    ):
        self.vehicle_id = vehicle_id
        self.name = name
        self.capacity = float(capacity)
        self.fuel_cost_per_km = float(
            fuel_cost_per_km
        )
        self.available = bool(available)

    def can_carry(self, total_demand):
        """
        Check whether the vehicle can carry
        the requested delivery demand.
        """

        return total_demand <= self.capacity

    def calculate_fuel_cost(self, distance):
        """
        Calculate estimated fuel cost.
        """

        return round(
            distance * self.fuel_cost_per_km,
            2
        )

    def to_dict(self):
        """
        Convert vehicle object into dictionary.
        """

        return {
            "id": self.vehicle_id,
            "name": self.name,
            "capacity": self.capacity,
            "fuel_cost_per_km": self.fuel_cost_per_km,
            "available": self.available
        }

    def __repr__(self):
        return (
            f"Vehicle("
            f"id={self.vehicle_id}, "
            f"name={self.name}, "
            f"capacity={self.capacity}"
            f")"
        )