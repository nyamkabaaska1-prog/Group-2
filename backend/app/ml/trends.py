"""Skill demand trend forecasting.

Aggregates job posts per ISO week per skill, then fits a simple linear regression
over a smoothed series to project the next N weeks. Lightweight and transparent —
swap in Prophet later if you have months of data.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def _week_key(d: datetime) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def aggregate_weekly(rows: list[tuple[datetime, str]]) -> dict[str, list[tuple[str, int]]]:
    """rows: (posted_at, skill_name). Returns {skill: [(week_key, count)]} sorted by week."""
    if not rows:
        return {}
    df = pd.DataFrame(rows, columns=["posted_at", "skill"])
    df["week"] = df["posted_at"].apply(_week_key)
    grouped = df.groupby(["skill", "week"]).size().reset_index(name="count")
    out: dict[str, list[tuple[str, int]]] = {}
    for skill, sub in grouped.groupby("skill"):
        out[str(skill)] = list(zip(sub["week"].tolist(), sub["count"].astype(int).tolist()))
    return out


def forecast(history: list[tuple[str, int]], horizon: int = 8) -> list[tuple[str, int]]:
    """Project next `horizon` weeks via linear regression on a 3-week rolling mean."""
    if len(history) < 3:
        return []
    weeks, counts = zip(*history)
    series = pd.Series(counts).rolling(window=3, min_periods=1).mean().values
    X = np.arange(len(series)).reshape(-1, 1)
    y = series

    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(series), len(series) + horizon).reshape(-1, 1)
    preds = model.predict(future_X)
    preds = np.maximum(preds, 0).round().astype(int)

    last_week = weeks[-1]
    future_weeks = _next_weeks(last_week, horizon)
    return list(zip(future_weeks, preds.tolist()))


def _next_weeks(last: str, n: int) -> list[str]:
    year, wk = last.split("-W")
    d = datetime.fromisocalendar(int(year), int(wk), 1)
    out = []
    for i in range(1, n + 1):
        nxt = d + timedelta(weeks=i)
        iso = nxt.isocalendar()
        out.append(f"{iso.year}-W{iso.week:02d}")
    return out
