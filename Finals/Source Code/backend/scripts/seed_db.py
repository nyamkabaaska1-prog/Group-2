"""Fetch jobs from Remotive, extract skills, persist to DB, and train salary model.

Run from the backend directory:
    python -m scripts.seed_db
    python -m scripts.seed_db --categories software-dev,data,devops --per-category 200
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.ingestion.remotive import fetch_jobs
from app.ml import salary as salary_mod
from app.ml import skills as skills_mod
from app.models import Job, Skill


def _ensure_skills(db) -> dict[str, Skill]:
    existing = {s.name: s for s in db.scalars(select(Skill)).all()}
    for name, category in skills_mod.all_skills():
        if name not in existing:
            s = Skill(name=name, category=category)
            db.add(s)
            existing[name] = s
    db.commit()
    return {s.name: s for s in db.scalars(select(Skill)).all()}


async def _ingest(categories: list[str], per_category: int) -> list:
    all_jobs = []
    if not categories:
        all_jobs.extend(await fetch_jobs(limit=per_category))
    else:
        for cat in categories:
            print(f"  fetching category={cat} ...", flush=True)
            try:
                all_jobs.extend(await fetch_jobs(category=cat, limit=per_category))
            except Exception as e:
                print(f"  WARN: {cat} failed: {e}")
    return all_jobs


def _save(db, raw_jobs, skills_lookup):
    inserted = 0
    updated = 0
    seen_ids: set[str] = set()
    for raw in raw_jobs:
        if not raw.title or not raw.description:
            continue
        if raw.external_id in seen_ids:
            continue
        seen_ids.add(raw.external_id)
        existing = db.scalar(select(Job).where(Job.external_id == raw.external_id))
        skill_names = skills_mod.extract(f"{raw.title} {raw.description}")
        seniority = salary_mod.infer_seniority(raw.title)

        if existing:
            existing.title = raw.title
            existing.salary_min = raw.salary_min
            existing.salary_max = raw.salary_max
            existing.skills = [skills_lookup[n] for n in skill_names if n in skills_lookup]
            existing.seniority = seniority
            updated += 1
        else:
            job = Job(
                source="remotive",
                external_id=raw.external_id,
                title=raw.title,
                company=raw.company,
                category=raw.category,
                location=raw.location,
                is_remote=raw.is_remote,
                seniority=seniority,
                description=raw.description[:5000],
                salary_min=raw.salary_min,
                salary_max=raw.salary_max,
                posted_at=raw.posted_at,
                url=raw.url,
                skills=[skills_lookup[n] for n in skill_names if n in skills_lookup],
            )
            db.add(job)
            inserted += 1
    db.commit()
    return inserted, updated


def _train(db) -> None:
    records = []
    for j in db.scalars(select(Job)).all():
        salary = None
        if j.salary_min and j.salary_max:
            salary = (j.salary_min + j.salary_max) / 2.0
        records.append(
            {
                "seniority": j.seniority,
                "is_remote": j.is_remote,
                "skills": [s.name for s in j.skills],
                "salary": salary,
            }
        )
    result = salary_mod.train(records)
    print(
        f"  salary model: n_labeled={result.n_samples} "
        f"mae={result.mae and round(result.mae, 0)} fallback={result.fallback_used}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--categories",
        default="software-dev,data,devops",
        help="comma-separated Remotive categories, or empty for all",
    )
    parser.add_argument("--per-category", type=int, default=150)
    args = parser.parse_args()

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]

    print("creating tables ...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("ensuring skills taxonomy ...")
        skills_lookup = _ensure_skills(db)

        print("ingesting jobs from Remotive ...")
        raw = asyncio.run(_ingest(cats, args.per_category))
        print(f"  fetched {len(raw)} raw jobs")

        inserted, updated = _save(db, raw, skills_lookup)
        print(f"  saved: inserted={inserted} updated={updated}")

        print("training salary model ...")
        _train(db)

        print("done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
