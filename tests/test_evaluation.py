import pandas as pd
from sklearn.linear_model import LogisticRegression

from core.evaluation import evaluate, sample_for_quantum
from core.pipelines import classical_pipeline


def test_evaluate_binary_metrics_and_confusion_matrix():
    X = pd.DataFrame({"x": range(12), "z": [0, 1] * 6})
    y = pd.Series([0, 1] * 6)
    result = evaluate(classical_pipeline(LogisticRegression()), X, y, "classification", cv=2)
    assert "roc_auc" in result
    assert len(result["confusion_matrix"]) == 2


def test_classification_quantum_sample_is_stratified_and_capped():
    X = pd.DataFrame({"x": range(20)})
    y = pd.Series([0] * 15 + [1] * 5)
    sampled_X, sampled_y = sample_for_quantum(X, y, 10, "classification")
    assert len(sampled_X) == 10
    assert set(sampled_y) == {0, 1}
