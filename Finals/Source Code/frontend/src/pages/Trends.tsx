import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, SkillDemand, TrendSeries } from "../api";

export default function Trends() {
  const [skills, setSkills] = useState<SkillDemand[]>([]);
  const [active, setActive] = useState<string>("");
  const [series, setSeries] = useState<TrendSeries | null>(null);

  useEffect(() => {
    api.skillsDemand(20).then((d) => {
      setSkills(d);
      if (d.length && !active) setActive(d[0].skill);
    });
  }, []);

  useEffect(() => {
    if (!active) return;
    api.trends(active, 8).then(setSeries).catch(console.error);
  }, [active]);

  const merged = series
    ? [
        ...series.history.map((p) => ({ week: p.week, history: p.count, forecast: null as number | null })),
        ...series.forecast.map((p) => ({ week: p.week, history: null as number | null, forecast: p.count })),
      ]
    : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Skill Demand Trends</h1>

      <div className="flex flex-wrap gap-2">
        {skills.map((s) => (
          <button
            key={s.skill}
            onClick={() => setActive(s.skill)}
            className={`px-3 py-1 text-xs rounded-full border ${
              active === s.skill
                ? "bg-brand-600 border-brand-500 text-white"
                : "bg-slate-900 border-slate-800 text-slate-300 hover:border-brand-500/50"
            }`}
          >
            {s.skill} <span className="opacity-60">· {s.count}</span>
          </button>
        ))}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-slate-300 mb-1">
          {active || "Pick a skill"} — weekly mentions
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Solid line is observed; dashed is an 8-week linear-regression forecast over the 3-week
          moving average.
        </p>
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={merged}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="week" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
              cursor={{ stroke: "#475569" }}
            />
            <Legend />
            <Line type="monotone" dataKey="history" name="observed" stroke="#22d3ee" strokeWidth={2} dot={false} connectNulls />
            <Line
              type="monotone"
              dataKey="forecast"
              name="forecast"
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
