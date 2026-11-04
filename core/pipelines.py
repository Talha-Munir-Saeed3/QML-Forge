import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA


def classical_pipeline(model):
    # Imputing/scaling inside the pipeline keeps CV free of leakage.
    return Pipeline([("impute", SimpleImputer(strategy="median")),
                     ("scale", StandardScaler()), ("model", model)])


def quantum_pipeline(model, n_qubits, n_features):
    k = min(n_qubits, n_features)
    return Pipeline([("impute", SimpleImputer(strategy="median")),
                     ("scale", StandardScaler()), ("pca", PCA(n_components=k)),
                     ("angle", MinMaxScaler((0, np.pi))), ("model", model)])
