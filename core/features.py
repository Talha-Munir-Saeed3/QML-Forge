import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


def build_xy(df, target, task):
    y = df[target]
    X = df.drop(columns=[target])
    X = X.drop(columns=X.select_dtypes(include=["datetime"]).columns)
    X = pd.get_dummies(X, dtype=float)
    if task == "classification":
        y = pd.Series(LabelEncoder().fit_transform(y.astype(str)), index=y.index)
    return X, y


def quantum_readiness(X, task, max_qubits=8, row_cap=300):
    """Plain-language notes on how well this dataset fits a simulated quantum model."""
    n_rows, n_feat = X.shape
    notes = []
    q = int(min(max_qubits, max(2, n_feat)))
    notes.append(f"{n_feat} features after encoding -> PCA to {q} qubits is suggested.")
    if n_rows > row_cap:
        notes.append(f"{n_rows} rows is large for kernel simulation (O(n²) states); "
                     f"quantum models will use a sample of ~{row_cap} rows.")
    if n_feat > max_qubits:
        notes.append("Features exceed the qubit budget, so PCA will discard some variance.")
    return q, notes
