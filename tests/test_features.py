import pandas as pd

from core.features import build_xy, quantum_readiness


def test_build_xy_encodes_features_and_labels():
    X, y = build_xy(pd.DataFrame({"city": ["a", "b"], "target": ["yes", "no"]}),
                    "target", "classification")
    assert set(y) == {0, 1}
    assert "city_a" in X and "city_b" in X


def test_quantum_readiness_reports_cap():
    X = pd.DataFrame([[1, 2], [3, 4], [5, 6]])
    q, notes = quantum_readiness(X, "classification", max_qubits=2, row_cap=2)
    assert q == 2
    assert any("sample" in note for note in notes)
