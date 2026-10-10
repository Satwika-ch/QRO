"""
Quantum simulator for QuantumRoute.

Uses the QuantumCircuit class to simulate
small quantum circuits using NumPy.
"""

import numpy as np

from .quantum_circuit import QuantumCircuit


class QuantumSimulator:
    """
    Lightweight quantum simulator.
    """

    def __init__(self, num_qubits):

        self.num_qubits = num_qubits

        self.circuit = QuantumCircuit(
            num_qubits
        )

    def create_superposition(self):

        """
        Put every qubit into superposition.
        """

        for qubit in range(
            self.num_qubits
        ):

            self.circuit.hadamard(
                qubit
            )

    def apply_phase(
        self,
        qubit,
        theta
    ):

        """
        Apply a phase rotation.
        """

        self.circuit.phase_rotation(
            qubit,
            theta
        )

    def apply_x(self, qubit):

        """
        Apply Pauli-X gate.
        """

        self.circuit.pauli_x(
            qubit
        )

    def get_probabilities(self):

        """
        Return measurement probabilities.
        """

        return (
            self.circuit
            .measure_probabilities()
        )

    def measure(self, shots=1000):

        """
        Perform repeated measurements.

        Parameters
        ----------
        shots : int
            Number of measurements.
        """

        if shots <= 0:

            raise ValueError(
                "Shots must be greater than zero."
            )

        probabilities = (
            self.circuit.probabilities()
        )

        states = np.arange(
            len(probabilities)
        )

        samples = np.random.choice(
            states,
            size=shots,
            p=probabilities
        )

        counts = {}

        for sample in samples:

            binary = format(
                int(sample),
                f"0{self.num_qubits}b"
            )

            counts[binary] = (
                counts.get(binary, 0) + 1
            )

        return counts

    def reset(self):

        """
        Reset the simulator.
        """

        self.circuit.reset()


if __name__ == "__main__":

    simulator = QuantumSimulator(
        num_qubits=2
    )

    simulator.create_superposition()

    print(
        "\n========== QUANTUM SIMULATOR =========="
    )

    print("\nProbabilities:")

    probabilities = (
        simulator.get_probabilities()
    )

    for state, probability in probabilities.items():

        if probability > 0.000001:

            print(
                f"|{state}> : "
                f"{probability:.4f}"
            )

    print("\nMeasurement results:")

    results = simulator.measure(
        shots=1000
    )

    for state, count in sorted(
        results.items()
    ):

        print(
            f"|{state}> : {count}"
        )