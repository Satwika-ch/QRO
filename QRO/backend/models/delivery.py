"""
Delivery model for QuantumRoute.
"""


class Delivery:
    """
    Represents a delivery request.

    A delivery has:
        - unique ID
        - customer name
        - destination
        - demand
        - delivery time window
    """

    def __init__(
        self,
        delivery_id,
        location_id,
        customer,
        demand,
        earliest=0,
        latest=100
    ):
        self.delivery_id = delivery_id
        self.location_id = location_id
        self.customer = customer
        self.demand = float(demand)
        self.earliest = float(earliest)
        self.latest = float(latest)

    def to_dict(self):
        """
        Convert the delivery object into a dictionary.
        """

        return {
            "id": self.delivery_id,
            "location_id": self.location_id,
            "customer": self.customer,
            "demand": self.demand,
            "earliest": self.earliest,
            "latest": self.latest
        }

    def __repr__(self):
        return (
            f"Delivery("
            f"id={self.delivery_id}, "
            f"location={self.location_id}, "
            f"demand={self.demand}"
            f")"
        )