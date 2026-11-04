from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                              GradientBoostingClassifier, GradientBoostingRegressor)
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture

CLASSIFIERS = {
    "Logistic Regression": lambda: LogisticRegression(max_iter=1000),
    "KNN": lambda: KNeighborsClassifier(),
    "Naive Bayes": lambda: GaussianNB(),
    "Decision Tree": lambda: DecisionTreeClassifier(random_state=0),
    "Random Forest": lambda: RandomForestClassifier(random_state=0),
    "Gradient Boosting": lambda: GradientBoostingClassifier(random_state=0),
    "SVM (RBF)": lambda: SVC(),
    "MLP": lambda: MLPClassifier(max_iter=500, random_state=0),
}
REGRESSORS = {
    "Linear Regression": lambda: LinearRegression(),
    "Ridge": lambda: Ridge(),
    "Lasso": lambda: Lasso(),
    "KNN": lambda: KNeighborsRegressor(),
    "Decision Tree": lambda: DecisionTreeRegressor(random_state=0),
    "Random Forest": lambda: RandomForestRegressor(random_state=0),
    "Gradient Boosting": lambda: GradientBoostingRegressor(random_state=0),
    "SVR (RBF)": lambda: SVR(),
    "MLP": lambda: MLPRegressor(max_iter=500, random_state=0),
}
CLUSTERERS = {
    "K-Means": lambda k: KMeans(n_clusters=k, n_init=10, random_state=0),
    "Agglomerative": lambda k: AgglomerativeClustering(n_clusters=k),
    "Gaussian Mixture": lambda k: GaussianMixture(n_components=k, random_state=0),
    "DBSCAN": lambda k: DBSCAN(),
}

try:
    from xgboost import XGBClassifier, XGBRegressor
    CLASSIFIERS["XGBoost"] = lambda: XGBClassifier(eval_metric="logloss", verbosity=0)
    REGRESSORS["XGBoost"] = lambda: XGBRegressor(verbosity=0)
except ImportError:
    pass
