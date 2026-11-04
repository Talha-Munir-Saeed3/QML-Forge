import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from .optimization import optimization_steps


def classical_pipeline(model, optimization=None, task="classification"):
    # Imputing/scaling inside the pipeline keeps CV free of leakage.
    return Pipeline(optimization_steps(optimization, task) + [("model", model)])


def quantum_pipeline(model, n_qubits, n_features, optimization=None, task="classification"):
    k = min(n_qubits, n_features)
    steps = optimization_steps(optimization, task)
    steps.extend([("pca", PCA(n_components=k)),
                  ("angle", MinMaxScaler((0, np.pi)))])
    steps.append(("model", model))
    return Pipeline(steps)
