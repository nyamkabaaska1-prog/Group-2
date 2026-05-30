# AI Job Market Analyzer

End-to-end ML web app that ingests real job postings, extracts skills, predicts
salaries, and forecasts skill-demand trends.

```
React (Vite + TS + Tailwind + Recharts)
        |
        v
FastAPI (Python 3.11+)
        |
        v
ML Engine
  - scikit-learn  (gradient-boosted salary regressor + trend forecast)
  - pandas/numpy  (aggregations, weekly rollups)
  - regex NLP     (curated skills taxonomy with aliases)
        |
        v
SQLite (SQLAlchemy 2)
```

## Features

- Live ingestion from the public Remotive jobs API (no auth needed).
- NLP skill extraction against an ~80-entry taxonomy (languages, frameworks,
  cloud, data, ML, databases) with alias regex matching.
- Salary prediction model (GradientBoostingRegressor) over seniority, remote
  flag, and one-hot skill features; falls back to a per-seniority median when
  labeled data is sparse.
- Time-series forecast of weekly skill mentions (linear regression on a 3-week
  rolling mean, 8-week horizon).
- Interactive React dashboard: KPIs, demand bar charts, category pie, trend
  line chart with observed + forecast, job list with filters, and an
  interactive salary predictor.

## Setup (Windows / PowerShell)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# fetch ~450 real jobs across software-dev / data / devops and train the model
python -m scripts.seed_db

# start the API
uvicorn app.main:app --reload --port 8000
```

API docs at http://127.0.0.1:8000/docs

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api/*` to the backend.

## Demo flow (~5 minutes)

1. **Dashboard** — total jobs, avg salary, top category, remote %; demand bar
   chart + category pie. Shows the ingestion + aggregation pipeline working.
2. **Skills** — bar chart of top 30 skills by mentions, and a second bar of
   average salary by skill (sklearn aggregation, real numbers).
3. **Trends** — click any skill; observed weekly counts plus an 8-week
   forecast. Mention this is a transparent linear baseline and could be
   upgraded to Prophet/ARIMA with more historical data.
4. **Salary Predictor** — type a title (e.g., "Senior ML Engineer"), pick
   skills, predict. Show that the model infers seniority from the title and
   explains its drivers.
5. **Jobs** — search + filter list backed by SQL through SQLAlchemy.

## Project structure

```
backend/
  app/
    main.py              FastAPI app + lifespan + CORS
    config.py            Pydantic settings (.env)
    database.py          SQLAlchemy engine + session
    models.py            Job, Skill, job_skills association
    schemas.py           Pydantic response/request schemas
    ingestion/
      remotive.py        Async HTTP client + salary regex parser
    ml/
      skills.py          Regex skill extractor over JSON taxonomy
      salary.py          GBR pipeline + persistence + baseline fallback
      trends.py          Weekly aggregation + linear forecast
    routers/
      jobs.py            /api/jobs (list, get)
      analytics.py       /api/analytics/{stats, skills/demand, trends, categories}
      predict.py         /api/predict/salary
    data/
      skills_taxonomy.json
  scripts/
    seed_db.py           Fetch -> extract -> persist -> train

frontend/
  src/
    pages/               Dashboard, Jobs, Skills, Trends, SalaryPredictor
    components/          Layout, StatCard
    api.ts               typed fetch client
```

## What to say if a teacher asks "why these choices?"

- **Why Remotive vs scraping LinkedIn?** ToS-safe, no auth, real data. The
  ingestion layer is isolated in `app/ingestion/` so adding Adzuna, Remotive,
  or a Kaggle dump later is just one more file.
- **Why GBR vs deep learning?** GradientBoosting wins on small tabular data
  and gives interpretable feature importances — appropriate for the size of
  the labeled subset.
- **Why linear forecast vs Prophet?** Prophet shines with >12 months of
  history. With one ingestion snapshot we have weeks of data; a transparent
  rolling-mean regression is honest. The interface is swappable.
- **Why SQLite?** Zero setup for grading. The SQLAlchemy 2 layer is
  database-agnostic — switching to Postgres is one connection string.
