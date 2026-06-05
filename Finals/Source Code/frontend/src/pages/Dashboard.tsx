import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, DashboardStats, SkillDemand } from "../api";
import { StatCard } from "../components/StatCard";

const PIE_COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#ef4444", "#a855f7", "#ec4899"];

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [demand, setDemand] = useState<SkillDemand[]>([]);
  const [cats, setCats] = useState<{ category: string; count: number }[]>([]);

  useEffect(() => {
    api.stats().then(setStats).catch(console.error);
    api.skillsDemand(12).then(setDemand).catch(console.error);
    api.categories().then((c) => setCats(c.slice(0, 6))).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Jobs" value={stats ? stats.total_jobs.toLocaleString() : "—"} />
        <StatCard label="Tracked Skills" value={stats ? String(stats.total_skills) : "—"} />
        <StatCard
          label="Avg Salary"
          value={
            stats?.avg_salary
              ? `$${Math.round(stats.avg_salary).toLocaleString()}`
              : "—"
          }
          hint="midpoint of parsed ranges"
        />
        <StatCard
          label="Remote"
          value={stats ? `${stats.remote_pct}%` : "—"}
          hint={stats?.top_category ? `Top: ${stats.top_category}` : undefined}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 lg:col-span-2">
          <h2 className="text-sm font-medium text-slate-300 mb-4">Top skill demand</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={demand}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="skill" stroke="#94a3b8" angle={-25} textAnchor="end" height={70} />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
                cursor={{ fill: "#1e293b" }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h2 className="text-sm font-medium text-slate-300 mb-4">Top categories</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={cats} dataKey="count" nameKey="category" innerRadius={50} outerRadius={90} paddingAngle={2}>
                {cats.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            </PieChart>
          </ResponsiveContainer>
          <ul className="text-xs text-slate-400 space-y-1 mt-2">
            {cats.map((c, i) => (
              <li key={c.category} className="flex justify-between">
                <span>
                  <span
                    className="inline-block w-2 h-2 mr-2 rounded-full"
                    style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                  />
                  {c.category || "Other"}
                </span>
                <span>{c.count}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {!stats && (
        <div className="text-amber-400 text-sm">
          No data yet — run <code className="bg-slate-800 px-1.5 py-0.5 rounded">python -m scripts.seed_db</code> in the backend.
        </div>
      )}
    </div>
  );
}
