import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, SkillDemand } from "../api";

export default function Skills() {
  const [data, setData] = useState<SkillDemand[]>([]);

  useEffect(() => {
    api.skillsDemand(30).then(setData).catch(console.error);
  }, []);

  const withSalary = data.filter((d) => d.avg_salary);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Skills</h1>
      <p className="text-sm text-slate-400">
        Counts come from regex-based skill extraction; salaries are averaged across postings that
        include a parsable salary range.
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-slate-300 mb-4">Demand (mention count)</h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" stroke="#94a3b8" />
            <YAxis type="category" dataKey="skill" stroke="#94a3b8" width={80} />
            <Tooltip
              contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
              cursor={{ fill: "#1e293b" }}
            />
            <Bar dataKey="count" fill="#22d3ee" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-slate-300 mb-4">Avg salary by skill</h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={withSalary}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="skill" stroke="#94a3b8" angle={-35} textAnchor="end" height={80} />
            <YAxis stroke="#94a3b8" tickFormatter={(v) => `$${Math.round(v / 1000)}k`} />
            <Tooltip
              contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
              formatter={(v: number) => `$${Math.round(v).toLocaleString()}`}
              cursor={{ fill: "#1e293b" }}
            />
            <Bar dataKey="avg_salary" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
