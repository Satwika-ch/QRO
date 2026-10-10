"""
Basic quantum circuit implementation for QuantumRoute.

This is a lightweight educational quantum simulator.
It uses NumPy to represent quantum states.

Supported gates:
    - Hadamard (H)
    - Pauli-X (X)
    - Phase rotation (RZ)
"""

import numpy as np


class QuantumCircuit:
    """
    Simple state-vector quantum circuit.
    """

    def __init__(self, num_qubits):
        if num_qubits <= 0:
            raise ValueError(
                "Number of qubits must be greater than zero."
            )

        self.num_qubits = num_qubits

        self.dimension = 2 ** num_qubits

        # Start in |000...0>
        self.state = np.zeros(
            self.dimension,
            dtype=complex
        )

        self.state[0] = 1.0

    def hadamard(self, qubit):
        """
        Apply Hadamard gate to a qubit.
        """

        self._validate_qubit(qubit)

        self._apply_single_qubit_gate(
            qubit,
            np.array([
                [1, 1],
                [1, -1]
            ], dtype=complex) / np.sqrt(2)
        )

    def pauli_x(self, qubit):
        """
        Apply Pauli-X gate.
        """

        self._validate_qubit(qubit)

        self._apply_single_qubit_gate(
            qubit,
            np.array([
                [0, 1],
                [1, 0]
            ], dtype=complex)
        )

    def phase_rotation(self, qubit, theta):
        """
        Apply phase rotation.
        """

        self._validate_qubit(qubit)

        gate = np.array([
            [1, 0],
            [0, np.exp(1j * theta)]
        ], dtype=complex)

        self._apply_single_qubit_gate(
            qubit,
            gate
        )

    def _apply_single_qubit_gate(
        self,
        qubit,
        gate
    ):
        """
        Apply a 2x2 gate to one qubit.
        """

        new_state = self.state.copy()

        for index in range(self.dimension):

            # Only process states where target bit = 0
            if ((index >> qubit) & 1) == 0:

                partner = index | (
                    1 << qubit
                )

                a = self.state[index]
                b = self.state[partner]

                new_state[index] = (
                    gate[0, 0] * a
                    + gate[0, 1] * b
                )

                new_state[partner] = (
                    gate[1, 0] * a
                    + gate[1, 1] * b
                )

        self.state = new_state

    def probabilities(self):
        """
        Return probability of every basis state.
        """

        return np.abs(self.state) ** 2

    def measure_probabilities(self):
        """
        Return probabilities in readable format.
        """

        probabilities = self.probabilities()

        result = {}

        for index, probability in enumerate(
            probabilities
        ):

            binary = format(
                index,
                f"0{self.num_qubits}b"
            )

            result[binary] = float(
                probability
            )

        return result

    def _validate_qubit(self, qubit):

        if not isinstance(qubit, int):

            raise TypeError(
                "Qubit index must be an integer."
            )

        if qubit < 0 or qubit >= self.num_qubits:

            raise ValueError(
                f"Qubit must be between 0 and "
                f"{self.num_qubits - 1}."
            )

    def reset(self):
        """
        Reset circuit to |000...0>.
        """

        self.state = np.zeros(
            self.dimension,
            dtype=complex
        )

        self.state[0] = 1.0

    def get_state(self):
        """
        Return the quantum state vector.
        """

        return self.state.copy()


if __name__ == "__main__":

    circuit = QuantumCircuit(2)

    circuit.hadamard(0)
    circuit.hadamard(1)

    print("\n========== QUANTUM CIRCUIT ==========")

    print("Number of qubits:")
    print(circuit.num_qubits)

    print("\nProbabilities:")

    for state, probability in (
        circuit.measure_probabilities().items()
    ):

        if probability > 0.000001:

            print(
                f"|{state}> : "
                f"{probability:.4f}"
            )