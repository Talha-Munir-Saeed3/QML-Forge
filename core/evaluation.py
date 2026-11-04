import numpy as np
import pandas as pd
from sklearn.model_selection import cross_validate, cross_val_predict, StratifiedKFold, KFold
from sklearn.metrics import silhouette_score, davies_bouldin_score, confusion_matrix
from .pipelines import quantum_pipeline

PRIMARY = {"classification": "f1", "regression": "r2", "clustering": "silhouette"}


def sample_for_quantum(X, y, cap, task, seed=0):
    """Return a deterministic cap-sized sample, stratified for classification."""
    if len(X) <= cap:
        return X, y
    if task == "classification":
        from sklearn.model_selection import train_test_split
        idx, _ = train_test_split(
            np.arange(len(X)), train_size=cap, random_state=seed,
            stratify=np.asarray(y),
        )
        return X.iloc[idx], y.iloc[idx]
    idx = X.sample(cap, random_state=seed).index
    return X.loc[idx], y.loc[idx] if y is not None else None


def evaluate(pipe, X, y, task, cv=3, seed=0):
    if task == "classification":
        cv = max(2, min(cv, int(np.bincount(y).min())))
        splitter = StratifiedKFold(cv, shuffle=True, random_state=seed)
        scoring = {"accuracy": "accuracy", "precision": "precision_macro",
                   "recall": "recall_macro", "f1": "f1_macro"}
        if y.nunique() == 2:
            scoring["roc_auc"] = "roc_auc"
        sign = {}
    else:
        splitter = KFold(cv, shuffle=True, random_state=seed)
        scoring = {"mae": "neg_mean_absolute_error", "rmse": "neg_root_mean_squared_error", "r2": "r2"}
        sign = {"mae": -1, "rmse": -1}
    res = cross_validate(pipe, X, y, cv=splitter, scoring=scoring)
    out = {k: float(sign.get(k, 1) * res[f"test_{k}"].mean()) for k in scoring}
    out["fit_time_s"] = float(res["fit_time"].mean())
    if task == "classification":
        predicted = cross_val_predict(pipe, X, y, cv=splitter, method="predict")
        out["confusion_matrix"] = confusion_matrix(y, predicted).tolist()
        if hasattr(pipe, "named_steps") and hasattr(pipe.named_steps.get("model"), "feature_importances_"):
            out["feature_importance"] = pipe.named_steps["model"].feature_importances_.tolist()
    return out


def evaluate_clustering(pipe, X):
    labels = pipe.fit_predict(X)
    Xt = pipe[:-1].transform(X)
    out = {"clusters_found": int(len(set(labels)) - (1 if -1 in labels else 0))}
    if len(set(labels)) > 1:
        out["silhouette"] = float(silhouette_score(Xt, labels))
        out["davies_bouldin"] = float(davies_bouldin_score(Xt, labels))
    return out


def qubit_sweep(X, y, qubit_range, cv=3):
    """Accuracy vs qubits: quantum-kernel SVM vs classical RBF SVM on identical PCA features."""
    from sklearn.svm import SVC
    from .quantum_models import QuantumKernelSVC
    rows = []
    for q in qubit_range:
        qp = quantum_pipeline(QuantumKernelSVC(n_qubits=q), q, X.shape[1])
        cp = quantum_pipeline(SVC(), q, X.shape[1])  # same PCA + [0, pi] scaling, classical kernel
        rows.append({"qubits": q,
                     "quantum_kernel_acc": evaluate(qp, X, y, "classification", cv)["accuracy"],
                     "classical_rbf_acc": evaluate(cp, X, y, "classification", cv)["accuracy"]})
    return pd.DataFrame(rows).set_index("qubits")
