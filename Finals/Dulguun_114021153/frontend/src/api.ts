const BASE = "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} ${text}`);
  }
  return res.json() as Promise<T>;
}

export type Skill = { id: number; name: string; category: string };

export type Job = {
  id: number;
  title: string;
  company: string;
  category: string;
  location: string;
  is_remote: boolean;
  seniority: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_predicted: number | null;
  posted_at: string;
  url: string;
  skills: Skill[];
};

export type JobsPage = { total: number; items: Job[] };

export type SkillDemand = {
  skill: string;
  category: string;
  count: number;
  avg_salary: number | null;
};

export type TrendPoint = { week: string; count: number };
export type TrendSeries = {
  skill: string;
  history: TrendPoint[];
  forecast: TrendPoint[];
};

export type DashboardStats = {
  total_jobs: number;
  total_skills: number;
  avg_salary: number | null;
  top_category: string;
  remote_pct: number;
};

export type PredictResponse = {
  predicted_salary: number;
  seniority: string;
  confidence: string;
  drivers: string[];
};

export const api = {
  stats: () => http<DashboardStats>("/analytics/stats"),
  skillsDemand: (limit = 20) =>
    http<SkillDemand[]>(`/analytics/skills/demand?limit=${limit}`),
  categories: () =>
    http<{ category: string; count: number }[]>("/analytics/categories"),
  trends: (skill: string, horizon = 8) =>
    http<TrendSeries>(`/analytics/trends/${encodeURIComponent(skill)}?horizon=${horizon}`),
  jobs: (params: { q?: string; skill?: string; seniority?: string; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
    });
    return http<JobsPage>(`/jobs?${qs.toString()}`);
  },
  predictSalary: (body: { title: string; skills: string[]; is_remote: boolean; location?: string }) =>
    http<PredictResponse>("/predict/salary", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
