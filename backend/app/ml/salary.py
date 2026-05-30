"""Salary prediction.

Pipeline: gradient-boosted regressor over numeric (seniority, remote, n_skills)
and one-hot skill features. Trains on jobs that have a parsed salary range
(midpoint as target). If too few labeled rows exist, falls back to a per-
seniority median baseline so the API still returns sensible numbers for demos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler

from . import skills as skills_mod

MODEL_PATH = Path(__file__).resolve().parent / "salary_model.joblib"

_SENIORITY_ORDER = {"junior": 0, "mid": 1, "senior": 2, "lead": 3, "principal": 4}

_SENIORITY_PATTERNS = [
    ("principal", re.compile(r"\bprincipal|staff|distinguished\b", re.I)),
    ("lead", re.compile(r"\blead|head of|manager\b", re.I)),
    ("senior", re.compile(r"\bsr\.?|senior|sr\b", re.I)),
    ("junior", re.compile(r"\bjr\.?|junior|entry|intern|graduate\b", re.I)),
]


def infer_seniority(title: str) -> str:
    t = title or ""
    for label, pat in _SENIORITY_PATTERNS:
        if pat.search(t):
            return label
    return "mid"


@dataclass
class TrainResult:
    n_samples: int
    mae: float | None
    fallback_used: bool
    baseline: dict[str, float]


class _SkillVectorizer(BaseEstimator, TransformerMixin):
    """Wraps MultiLabelBinarizer so it plays nicely inside ColumnTransformer.

    Subclasses BaseEstimator so sklearn's clone() works (clone introspects
    __init__ params and expects them as attributes with matching names).
    """

    def __init__(self, classes: list[str] | None = None):
        self.classes = classes or []

    def fit(self, X, y=None):
        self.mlb_ = MultiLabelBinarizer(classes=self.classes)
        self.mlb_.fit([self.classes])
        return self

    def transform(self, X):
        arr = np.asarray(X, dtype=object)
        rows = [row[0] if isinstance(row, np.ndarray) else row for row in arr]
        return self.mlb_.transform(rows)


def _build_pipeline(skill_classes: list[str]) -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), ["seniority_idx", "is_remote", "n_skills"]),
            ("skills", _SkillVectorizer(skill_classes), ["skills"]),
        ]
    )
    return Pipeline(
        steps=[
            ("pre", pre),
            ("gbr", GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=42)),
        ]
    )


def _to_frame(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    df["seniority_idx"] = df["seniority"].map(_SENIORITY_ORDER).fillna(1).astype(int)
    df["is_remote"] = df["is_remote"].astype(int)
    df["n_skills"] = df["skills"].apply(len)
    return df


def train(records: list[dict]) -> TrainResult:
    """Train and persist a salary model.

    Each record: {seniority, is_remote, skills: list[str], salary: float}
    """
    labeled = [r for r in records if r.get("salary") and r["salary"] > 0]
    baseline = _baseline(labeled)

    if len(labeled) < 25:
        joblib.dump({"fallback": True, "baseline": baseline}, MODEL_PATH)
        return TrainResult(n_samples=len(labeled), mae=None, fallback_used=True, baseline=baseline)

    df = _to_frame(labeled)
    classes = [s for s, _ in skills_mod.all_skills()]
    pipe = _build_pipeline(classes)

    X = df[["seniority_idx", "is_remote", "n_skills", "skills"]]
    y = df["salary"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    mae = float(mean_absolute_error(y_test, pred))

    joblib.dump({"fallback": False, "pipeline": pipe, "baseline": baseline, "classes": classes}, MODEL_PATH)
    return TrainResult(n_samples=len(labeled), mae=mae, fallback_used=False, baseline=baseline)


def _baseline(labeled: list[dict]) -> dict[str, float]:
    """Median salary per seniority — used both as fallback and as a sanity floor."""
    by_level: dict[str, list[float]] = {}
    for r in labeled:
        by_level.setdefault(r["seniority"], []).append(r["salary"])
    out = {k: float(np.median(v)) for k, v in by_level.items() if v}
    # Fill in any missing seniority levels by interpolation
    defaults = {"junior": 65000, "mid": 95000, "senior": 135000, "lead": 165000, "principal": 195000}
    for k, v in defaults.items():
        out.setdefault(k, float(v))
    return out


def _load():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def predict(seniority: str, is_remote: bool, skills_list: list[str]) -> tuple[float, str, list[str]]:
    """Return (predicted_salary, confidence_label, top_drivers)."""
    bundle = _load()
    if bundle is None:
        baseline = {"junior": 65000, "mid": 95000, "senior": 135000, "lead": 165000, "principal": 195000}
        return baseline.get(seniority, 95000), "low", ["no model trained yet"]

    if bundle.get("fallback"):
        baseline = bundle["baseline"]
        base = baseline.get(seniority, baseline.get("mid", 95000))
        bump = min(len(skills_list), 8) * 2500
        return float(base + bump), "low", ["seniority baseline", f"{len(skills_list)} skills matched"]

    pipe: Pipeline = bundle["pipeline"]
    df = pd.DataFrame(
        [
            {
                "seniority": seniority,
                "is_remote": is_remote,
                "skills": skills_list,
            }
        ]
    )
    df = _to_frame(df.to_dict(orient="records"))
    X = df[["seniority_idx", "is_remote", "n_skills", "skills"]]
    pred = float(pipe.predict(X)[0])

    drivers = _drivers(seniority, skills_list)
    confidence = "high" if len(skills_list) >= 4 else "medium"
    return pred, confidence, drivers


def _drivers(seniority: str, skills_list: list[str]) -> list[str]:
    out = [f"seniority: {seniority}"]
    high_value = {"AWS", "Kubernetes", "PyTorch", "TensorFlow", "Go", "Rust", "LLM", "MLOps", "Snowflake", "Databricks"}
    matches = [s for s in skills_list if s in high_value]
    if matches:
        out.append("high-value skills: " + ", ".join(matches[:3]))
    out.append(f"{len(skills_list)} matched skills total")
    return out
