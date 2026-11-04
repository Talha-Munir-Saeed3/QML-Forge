import numpy as np

from core.quantum_models import QuantumKernelSVC


def test_quantum_kernel_classifier_fits_tiny_binary_data():
    X = np.array([[0.1, 0.2], [0.2, 0.1], [2.8, 2.9], [2.9, 2.8]])
    y = np.array([0, 0, 1, 1])
    model = QuantumKernelSVC(n_qubits=2, reps=1).fit(X, y)
    assert model.predict(X).shape == y.shape
