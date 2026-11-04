"""Replayable CSV cleaning. Every operation is logged so it can be undone/replayed."""
import json
import numpy as np
import pandas as pd


def standardize_columns(df):
    out = df.copy()
    out.columns = (out.columns.astype(str).str.strip().str.lower()
                   .str.replace(r"[^0-9a-z]+", "_", regex=True).str.strip("_"))
    return out


def strip_whitespace(df):
    out = df.copy()
    for c in out.select_dtypes(include="object"):
        out[c] = out[c].str.strip()
    return out


def standardize_case(df, cols, case="lower"):
    out = df.copy()
    for c in cols:
        out[c] = getattr(out[c].astype("string").str, case)().astype("object")
    return out


def drop_duplicates(df):
    return df.drop_duplicates().reset_index(drop=True)


def drop_columns(df, cols):
    return df.drop(columns=cols)


def to_numeric(df, cols):
    out = df.copy()
    for c in cols:
        cleaned = out[c].astype(str).str.replace(r"[^0-9eE.\-]", "", regex=True)
        out[c] = pd.to_numeric(cleaned, errors="coerce")
    return out


def parse_dates(df, cols):
    out = df.copy()
    for c in cols:
        out[c] = pd.to_datetime(out[c], errors="coerce")
    return out


def impute(df, cols, strategy="median"):
    out = df.copy()
    for c in cols:
        if strategy == "mean":
            out[c] = out[c].fillna(out[c].mean())
        elif strategy == "median":
            out[c] = out[c].fillna(out[c].median())
        elif strategy == "mode":
            m = out[c].mode()
            if len(m):
                out[c] = out[c].fillna(m.iloc[0])
    return out


def drop_missing_rows(df, cols):
    return df.dropna(subset=cols).reset_index(drop=True)


def clip_outliers(df, cols, k=1.5):
    out = df.copy()
    for c in cols:
        q1, q3 = out[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        out[c] = out[c].clip(q1 - k * iqr, q3 + k * iqr)
    return out


def encode(df, cols, method="one_hot"):
    if method == "one_hot":
        return pd.get_dummies(df, columns=cols, dtype=int)
    out = df.copy()
    for c in cols:
        out[c] = out[c].astype("category").cat.codes
    return out


OPS = {f.__name__: f for f in [
    standardize_columns, strip_whitespace, standardize_case, drop_duplicates,
    drop_columns, to_numeric, parse_dates, impute, drop_missing_rows,
    clip_outliers, encode]}


class CleaningPipeline:
    def __init__(self, df):
        self.original = df.copy()
        self.df = df.copy()
        self.log = []

    def apply(self, op, **params):
        self.df = OPS[op](self.df, **params)
        self.log.append({"op": op, "params": params})

    def undo(self):
        if self.log:
            self.log.pop()
            self.replay(self.log)

    def replay(self, steps, start=None):
        df = self.original.copy() if start is None else start.copy()
        for s in steps:
            df = OPS[s["op"]](df, **s["params"])
        self.df, self.log = df, list(steps)
        return df

    def to_json(self):
        return json.dumps(self.log, indent=2)
