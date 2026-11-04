from core.recommend import recommend


def test_recommend_small_imbalanced_classification():
    result = recommend("classification", 80, 4, [0.95, 0.05])
    names = [item["name"] for item in result]
    assert "Logistic Regression" in names
    assert all(item["reason"] for item in result)


def test_recommend_quantum_respects_limits():
    assert any("Quantum" in item["name"] for item in recommend("classification", 100, 4, [0.5, 0.5]))
    assert not any("Quantum" in item["name"] for item in recommend("classification", 301, 4, [0.5, 0.5]))
