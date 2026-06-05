from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..ml import trends as trends_mod
from ..models import Job, Skill, job_skills
from ..schemas import DashboardStats, SkillDemand, TrendPoint, TrendSeries

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)):
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    total_skills = db.scalar(select(func.count(Skill.id))) or 0

    avg_salary_row = db.execute(
        select(func.avg((Job.salary_min + Job.salary_max) / 2.0)).where(Job.salary_min.isnot(None))
    ).scalar()
    avg_salary = float(avg_salary_row) if avg_salary_row else None

    top_cat_row = db.execute(
        select(Job.category, func.count(Job.id).label("c"))
        .group_by(Job.category)
        .order_by(func.count(Job.id).desc())
        .limit(1)
    ).first()
    top_cat = top_cat_row[0] if top_cat_row else ""

    remote_count = db.scalar(select(func.count(Job.id)).where(Job.is_remote.is_(True))) or 0
    remote_pct = (remote_count / total_jobs * 100.0) if total_jobs else 0.0

    return DashboardStats(
        total_jobs=int(total_jobs),
        total_skills=int(total_skills),
        avg_salary=avg_salary,
        top_category=top_cat or "",
        remote_pct=round(remote_pct, 1),
    )


@router.get("/skills/demand", response_model=list[SkillDemand])
def skills_demand(db: Session = Depends(get_db), limit: int = Query(20, le=100)):
    rows = db.execute(
        select(
            Skill.name,
            Skill.category,
            func.count(job_skills.c.job_id).label("c"),
            func.avg((Job.salary_min + Job.salary_max) / 2.0).label("avg_salary"),
        )
        .select_from(Skill)
        .join(job_skills, Skill.id == job_skills.c.skill_id)
        .join(Job, Job.id == job_skills.c.job_id)
        .group_by(Skill.id)
        .order_by(func.count(job_skills.c.job_id).desc())
        .limit(limit)
    ).all()

    return [
        SkillDemand(
            skill=r[0],
            category=r[1],
            count=int(r[2]),
            avg_salary=float(r[3]) if r[3] else None,
        )
        for r in rows
    ]


@router.get("/categories")
def category_breakdown(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Job.category, func.count(Job.id))
        .group_by(Job.category)
        .order_by(func.count(Job.id).desc())
    ).all()
    return [{"category": r[0] or "Other", "count": int(r[1])} for r in rows]


@router.get("/trends/{skill}", response_model=TrendSeries)
def trend(skill: str, db: Session = Depends(get_db), horizon: int = 8):
    rows = db.execute(
        select(Job.posted_at, Skill.name)
        .join(job_skills, Job.id == job_skills.c.job_id)
        .join(Skill, Skill.id == job_skills.c.skill_id)
        .where(Skill.name == skill)
    ).all()

    series_map = trends_mod.aggregate_weekly([(r[0], r[1]) for r in rows])
    series = series_map.get(skill, [])
    series.sort(key=lambda x: x[0])
    history = [TrendPoint(week=w, count=c) for w, c in series]
    fc = trends_mod.forecast(series, horizon=horizon)
    forecast_points = [TrendPoint(week=w, count=c) for w, c in fc]
    return TrendSeries(skill=skill, history=history, forecast=forecast_points)
