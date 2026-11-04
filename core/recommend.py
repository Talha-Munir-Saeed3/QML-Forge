"""Small, deterministic rules for selecting a useful initial model shortlist."""

def recommend(task, n_rows, n_features, class_balance=None, missing_pct=0.0,
              categorical_share=0.0, quantum_cap=300, max_qubits=8):
    if task == "classification":
        if n_rows < 1000:
            names = ["KNN", "SVM (RBF)", "Logistic Regression"]
            reason = "small data favors local, margin-based, and linear baselines"
        else:
            names = ["Random Forest", "Gradient Boosting", "Logistic Regression"]
            reason = "larger data supports ensemble models and a stable baseline"
        if class_balance is not None and min(class_balance if isinstance(class_balance, (list, tuple)) else class_balance) < 0.2:
            names = ["Random Forest", "Gradient Boosting", "Logistic Regression"]
            reason = "class imbalance favors robust ensemble and weighted-capable baselines"
    elif task == "regression":
        names = (["Ridge", "Random Forest", "Gradient Boosting"] if n_rows >= 1000
                 else ["Ridge", "KNN", "Random Forest"])
        reason = "regularized and tree-based regressors provide complementary baselines"
    else:
        names = ["K-Means", "Agglomerative", "Gaussian Mixture"]
        reason = "these clustering methods cover centroid, hierarchical, and probabilistic views"
    if categorical_share > 0.5:
        reason += "; encoded categorical features should be checked for sparsity"
    if missing_pct > 0:
        reason += "; imputation is recommended because values are missing"
    result = [{"name": name, "reason": reason} for name in names]
    if task in ("classification", "regression") and n_rows <= quantum_cap and n_features <= max_qubits:
        result.append({"name": "Quantum Kernel SVC" if task == "classification"
                       else "Variational Quantum Regressor",
                       "reason": "dataset fits the simulated quantum row and qubit limits"})
    return result
