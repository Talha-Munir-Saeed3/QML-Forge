from sklearn.feature_selection import SelectKBest, SelectPercentile, VarianceThreshold, mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
import numpy as np


def feature_selector(settings, task="classification"):
    settings = settings or {}
    kind = settings.get("feature_selection", "none")
    if kind == "variance":
        return VarianceThreshold(float(settings.get("variance_threshold", 0.0)))
    if kind == "correlation":
        return SelectPercentile(mutual_info_classif if task == "classification" else mutual_info_regression,
                                percentile=max(1, min(100, int(settings.get("percentile", 80)))))
    if kind == "mutual_information":
        return SelectKBest(mutual_info_classif if task == "classification" else mutual_info_regression,
                           k=max(1, int(settings.get("k", 10))))
    return "passthrough"


def optimization_steps(settings, task="classification"):
    settings = settings or {}
    scaler = {"standard": StandardScaler(), "minmax": MinMaxScaler(),
              "none": "passthrough"}.get(settings.get("scaler", "standard"), StandardScaler())
    steps = [("impute", SimpleImputer(strategy="median")),
             ("scale", scaler)]
    selector = feature_selector(settings, task)
    if selector != "passthrough":
        steps.append(("select", selector))
    if settings.get("pca_components"):
        from sklearn.decomposition import PCA
        steps.append(("pca", PCA(n_components=int(settings["pca_components"]))))
    return steps


def hyperparameter_search(estimator, mode="none", n_iter=8, cv=3, seed=0):
    """Wrap an estimator in a small, safe default search space."""
    if mode == "none":
        return estimator
    params = {}
    model = estimator.named_steps.get("model", estimator) if hasattr(estimator, "named_steps") else estimator
    name = model.__class__.__name__
    if name in {"LogisticRegression", "SVC", "SVR", "Ridge", "Lasso"}:
        params = {"C": [0.1, 1.0, 10.0]} if name in {"LogisticRegression", "SVC", "SVR"} else {"alpha": [0.01, 0.1, 1.0]}
    elif "Forest" in name:
        params = {"n_estimators": [50, 100], "max_depth": [None, 5, 10]}
    elif "KNeighbors" in name:
        params = {"n_neighbors": [3, 5, 7]}
    if not params:
        return estimator
    search = GridSearchCV if mode == "grid" else RandomizedSearchCV
    kwargs = {"cv": cv, "n_jobs": -1, "random_state": seed} if search is RandomizedSearchCV else {"cv": cv, "n_jobs": -1}
    if search is RandomizedSearchCV:
        kwargs["n_iter"] = min(n_iter, max(1, int(np.prod([len(v) for v in params.values()]))))
    return search(estimator, {f"model__{key}": value for key, value in params.items()}, **kwargs)
