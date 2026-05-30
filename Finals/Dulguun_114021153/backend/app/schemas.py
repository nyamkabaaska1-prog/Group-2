from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    category: str
    location: str
    is_remote: bool
    seniority: str
    salary_min: float | None
    salary_max: float | None
    salary_predicted: float | None
    posted_at: datetime
    url: str
    skills: list[SkillOut]


class JobsPage(BaseModel):
    total: int
    items: list[JobOut]


class SkillDemand(BaseModel):
    skill: str
    category: str
    count: int
    avg_salary: float | None


class TrendPoint(BaseModel):
    week: str
    count: int


class TrendSeries(BaseModel):
    skill: str
    history: list[TrendPoint]
    forecast: list[TrendPoint]


class PredictRequest(BaseModel):
    title: str
    skills: list[str] = []
    is_remote: bool = True
    location: str = "Remote"


class PredictResponse(BaseModel):
    predicted_salary: float
    seniority: str
    confidence: str
    drivers: list[str]


class DashboardStats(BaseModel):
    total_jobs: int
    total_skills: int
    avg_salary: float | None
    top_category: str
    remote_pct: float
