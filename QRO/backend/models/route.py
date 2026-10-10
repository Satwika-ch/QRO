"""
Route model for QuantumRoute.
"""


class Route:
    """
    Represents a vehicle route.

    Example:

        DEPOT -> A -> B -> C -> DEPOT
    """

    def __init__(
        self,
        route_id,
        vehicle_id,
        locations=None
    ):
        self.route_id = route_id
        self.vehicle_id = vehicle_id
        self.locations = locations or []

        self.distance = 0.0
        self.cost = 0.0
        self.total_demand = 0.0
        self.is_valid = False

    def add_location(self, location_id):
        """
        Add a location to the route.
        """

        self.locations.append(location_id)

    def set_distance(self, distance):
        """
        Set total route distance.
        """

        self.distance = round(
            float(distance),
            2
        )

    def set_cost(self, cost):
        """
        Set total route cost.
        """

        self.cost = round(
            float(cost),
            2
        )

    def set_demand(self, demand):
        """
        Set total delivery demand.
        """

        self.total_demand = float(demand)

    def validate(self, vehicle_capacity):
        """
        Check whether the route satisfies
        vehicle capacity.
        """

        self.is_valid = (
            self.total_demand <= vehicle_capacity
        )

        return self.is_valid

    def to_dict(self):
        """
        Convert route object into dictionary.
        """

        return {
            "route_id": self.route_id,
            "vehicle_id": self.vehicle_id,
            "locations": self.locations,
            "distance": self.distance,
            "cost": self.cost,
            "total_demand": self.total_demand,
            "valid": self.is_valid
        }

    def __repr__(self):
        return (
            f"Route("
            f"id={self.route_id}, "
            f"vehicle={self.vehicle_id}, "
            f"distance={self.distance}"
            f")"
        )