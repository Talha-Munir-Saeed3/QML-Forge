"""Quantum models as sklearn estimators, so they run through the same CV/metrics as classical ones.
Inputs must be scaled to [0, pi] with n_features == n_qubits (see core/pipelines.py)."""
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.svm import SVC


def _state_fn(n_qubits, reps):
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev)
    def circuit(x):  # ZZ-style feature map: H, RZ, then entangling CNOT-RZ-CNOT blocks
        for _ in range(reps):
            for i in range(n_qubits):
                qml.Hadamard(wires=i)
                qml.RZ(x[i], wires=i)
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
                qml.RZ((np.pi - x[i]) * (np.pi - x[i + 1]), wires=i + 1)
                qml.CNOT(wires=[i, i + 1])
        return qml.state()
    return circuit


class QuantumKernelSVC(ClassifierMixin, BaseEstimator):
    """SVM whose kernel is the fidelity |<phi(a)|phi(b)>|^2 between quantum feature states."""
    def __init__(self, n_qubits=4, reps=2, C=1.0):
        self.n_qubits, self.reps, self.C = n_qubits, reps, C

    def _states(self, X):
        f = _state_fn(self.n_qubits, self.reps)
        return np.array([f(x) for x in np.asarray(X)])

    def _kernel(self, X):
        return np.abs(self._states(X).conj() @ self.train_states_.T) ** 2

    def fit(self, X, y):
        self.train_states_ = self._states(X)
        K = np.abs(self.train_states_.conj() @ self.train_states_.T) ** 2
        self.svc_ = SVC(kernel="precomputed", C=self.C).fit(K, y)
        self.classes_ = self.svc_.classes_
        return self

    def predict(self, X):
        return self.svc_.predict(self._kernel(X))

    def decision_function(self, X):
        return self.svc_.decision_function(self._kernel(X))


class _Variational(BaseEstimator):
    def __init__(self, n_qubits=4, layers=2, steps=40, lr=0.1, batch=24, seed=0):
        self.n_qubits, self.layers, self.steps = n_qubits, layers, steps
        self.lr, self.batch, self.seed = lr, batch, seed

    def _train(self, X, t):
        X = np.asarray(X)
        dev = qml.device("default.qubit", wires=self.n_qubits)

        @qml.qnode(dev)
        def circuit(w, x):
            qml.AngleEmbedding(x, wires=range(self.n_qubits), rotation="Y")
            qml.StronglyEntanglingLayers(w, wires=range(self.n_qubits))
            return qml.expval(qml.PauliZ(0))

        rng = np.random.default_rng(self.seed)
        shape = qml.StronglyEntanglingLayers.shape(n_layers=self.layers, n_wires=self.n_qubits)
        w = pnp.array(rng.normal(0, 0.1, size=shape), requires_grad=True)
        opt = qml.AdamOptimizer(self.lr)
        for _ in range(self.steps):
            idx = rng.choice(len(X), size=min(self.batch, len(X)), replace=False)
            xb, tb = X[idx], t[idx]

            def cost(w):
                preds = pnp.stack([circuit(w, x) for x in xb])
                return pnp.mean((preds - tb) ** 2)
            w = opt.step(cost, w)
        self.weights_, self._circuit = w, circuit

    def _raw(self, X):
        return np.array([float(self._circuit(self.weights_, x)) for x in np.asarray(X)])


class VariationalQuantumClassifier(ClassifierMixin, _Variational):
    """Binary classifier: parameterised circuit, <Z0> as the score, trained with Adam."""
    def fit(self, X, y):
        self.classes_ = np.unique(y)
        if len(self.classes_) != 2:
            raise ValueError("VQC here is binary; use Quantum Kernel SVM for multiclass.")
        t = np.where(np.asarray(y) == self.classes_[1], 1.0, -1.0)
        self._train(X, t)
        return self

    def decision_function(self, X):
        return self._raw(X)

    def predict(self, X):
        return self.classes_[(self._raw(X) > 0).astype(int)]


class VariationalQuantumRegressor(RegressorMixin, _Variational):
    def fit(self, X, y):
        y = np.asarray(y, dtype=float)
        self.lo_, self.hi_ = y.min(), y.max()
        span = (self.hi_ - self.lo_) or 1.0
        self._span = span
        self._train(X, 2 * (y - self.lo_) / span - 1)
        return self

    def predict(self, X):
        return (self._raw(X) + 1) / 2 * self._span + self.lo_


QUANTUM_CLASSIFIERS = {
    "Quantum Kernel SVM": lambda q: QuantumKernelSVC(n_qubits=q),
    "Variational Quantum Classifier": lambda q: VariationalQuantumClassifier(n_qubits=q),
}
QUANTUM_REGRESSORS = {
    "Variational Quantum Regressor": lambda q: VariationalQuantumRegressor(n_qubits=q),
}
