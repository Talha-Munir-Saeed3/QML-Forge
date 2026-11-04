import pandas as pd

from core.cleaning import CleaningPipeline


def test_cleaning_apply_undo_and_replay():
    source = pd.DataFrame({" Name ": [" A ", " A "], "value": ["1", "1"]})
    pipeline = CleaningPipeline(source)
    pipeline.apply("strip_whitespace")
    pipeline.apply("drop_duplicates")
    assert len(pipeline.df) == 1
    pipeline.undo()
    assert len(pipeline.df) == 2
    replayed = pipeline.replay([{"op": "to_numeric", "params": {"cols": ["value"]}}])
    assert replayed["value"].dtype.kind in "iu"


def test_cleaning_operations_cover_types_and_missing_values():
    frame = pd.DataFrame({"a": ["1", "2"], "b": ["x", None]})
    pipeline = CleaningPipeline(frame)
    pipeline.apply("to_numeric", cols=["a"])
    pipeline.apply("impute", cols=["b"], strategy="mode")
    pipeline.apply("encode", cols=["b"], method="ordinal")
    assert pipeline.df["a"].tolist() == [1, 2]
    assert pipeline.df["b"].isna().sum() == 0
