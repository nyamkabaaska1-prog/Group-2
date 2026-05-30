from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Job, Skill
from ..schemas import JobOut, JobsPage

router = APIRouter()


@router.get("", response_model=JobsPage)
def list_jobs(
    db: Session = Depends(get_db),
    q: str | None = None,
    skill: str | None = None,
    seniority: str | None = None,
    limit: int = Query(25, le=100),
    offset: int = 0,
):
    stmt = select(Job).options(selectinload(Job.skills))
    count_stmt = select(func.count(Job.id))

    if q:
        like = f"%{q}%"
        stmt = stmt.where((Job.title.ilike(like)) | (Job.company.ilike(like)))
        count_stmt = count_stmt.where((Job.title.ilike(like)) | (Job.company.ilike(like)))
    if seniority:
        stmt = stmt.where(Job.seniority == seniority)
        count_stmt = count_stmt.where(Job.seniority == seniority)
    if skill:
        stmt = stmt.join(Job.skills).where(Skill.name == skill)
        count_stmt = count_stmt.join(Job.skills).where(Skill.name == skill)

    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Job.posted_at.desc()).limit(limit).offset(offset)
    items = db.scalars(stmt).unique().all()
    return JobsPage(total=int(total), items=[JobOut.model_validate(j) for j in items])


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="job not found")
    return JobOut.model_validate(job)
