from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="remotive")
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), index=True)
    company: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64), default="")
    location: Mapped[str] = mapped_column(String(128), default="Remote")
    is_remote: Mapped[bool] = mapped_column(default=True)
    seniority: Mapped[str] = mapped_column(String(32), default="mid")
    description: Mapped[str] = mapped_column(Text)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_predicted: Mapped[float | None] = mapped_column(Float, nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    url: Mapped[str] = mapped_column(String(512), default="")

    skills: Mapped[list["Skill"]] = relationship(secondary=job_skills, back_populates="jobs")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), default="general")

    jobs: Mapped[list[Job]] = relationship(secondary=job_skills, back_populates="skills")
