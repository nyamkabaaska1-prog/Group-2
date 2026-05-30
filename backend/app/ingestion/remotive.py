"""Remotive public jobs API client.

Docs: https://remotive.com/api-documentation
No authentication required. Categories include software-dev, data, devops, design, etc.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from dateutil import parser as dateparser

from ..config import settings


@dataclass
class RawJob:
    external_id: str
    title: str
    company: str
    category: str
    location: str
    is_remote: bool
    description: str
    salary_min: float | None
    salary_max: float | None
    posted_at: datetime
    url: str


_TAG_RE = re.compile(r"<[^>]+>")
_SALARY_RE = re.compile(
    r"\$?\s*(\d{2,3})\s*[kK]?\s*[-–to]+\s*\$?\s*(\d{2,3})\s*[kK]?"
)


def _clean_html(raw: str) -> str:
    text = _TAG_RE.sub(" ", raw or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_salary(text: str) -> tuple[float | None, float | None]:
    if not text:
        return None, None
    m = _SALARY_RE.search(text)
    if not m:
        return None, None
    lo, hi = int(m.group(1)), int(m.group(2))
    if lo < 1000:
        lo *= 1000
    if hi < 1000:
        hi *= 1000
    if lo > hi or hi > 1_000_000:
        return None, None
    return float(lo), float(hi)


async def fetch_jobs(category: str | None = None, limit: int = 200) -> list[RawJob]:
    params: dict = {"limit": limit}
    if category:
        params["category"] = category
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(settings.remotive_api_url, params=params)
        r.raise_for_status()
        data = r.json()

    jobs: list[RawJob] = []
    for j in data.get("jobs", []):
        desc = _clean_html(j.get("description", ""))
        title = j.get("title", "").strip()
        salary_text = j.get("salary") or ""
        lo, hi = parse_salary(salary_text)
        if lo is None:
            lo, hi = parse_salary(desc[:1500])

        posted = j.get("publication_date") or j.get("created_at") or ""
        try:
            posted_dt = dateparser.parse(posted) if posted else datetime.utcnow()
            if posted_dt.tzinfo is not None:
                posted_dt = posted_dt.replace(tzinfo=None)
        except (ValueError, TypeError):
            posted_dt = datetime.utcnow()

        jobs.append(
            RawJob(
                external_id=str(j.get("id")),
                title=title,
                company=j.get("company_name", "").strip(),
                category=j.get("category", "").strip(),
                location=j.get("candidate_required_location", "Remote") or "Remote",
                is_remote=True,
                description=desc,
                salary_min=lo,
                salary_max=hi,
                posted_at=posted_dt,
                url=j.get("url", ""),
            )
        )
    return jobs
