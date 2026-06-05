import { useEffect, useState } from "react";
import { api, Job } from "../api";

export default function Jobs() {
  const [q, setQ] = useState("");
  const [seniority, setSeniority] = useState("");
  const [items, setItems] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    api
      .jobs({ q: q || undefined, seniority: seniority || undefined, limit: 30 })
      .then((p) => {
        setItems(p.items);
        setTotal(p.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Jobs</h1>

      <div className="flex gap-3 flex-wrap">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search title or company"
          className="bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm flex-1 min-w-[200px]"
        />
        <select
          value={seniority}
          onChange={(e) => setSeniority(e.target.value)}
          className="bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm"
        >
          <option value="">All levels</option>
          <option value="junior">Junior</option>
          <option value="mid">Mid</option>
          <option value="senior">Senior</option>
          <option value="lead">Lead</option>
          <option value="principal">Principal</option>
        </select>
        <button
          onClick={load}
          className="bg-brand-600 hover:bg-brand-500 px-4 py-2 rounded text-sm font-medium"
        >
          Search
        </button>
      </div>

      <div className="text-xs text-slate-500">{loading ? "Loading..." : `${total} jobs found`}</div>

      <div className="space-y-3">
        {items.map((j) => (
          <a
            key={j.id}
            href={j.url || "#"}
            target="_blank"
            rel="noreferrer"
            className="block bg-slate-900 border border-slate-800 hover:border-brand-500/50 rounded-lg p-4 transition-colors"
          >
            <div className="flex justify-between items-start gap-3">
              <div>
                <div className="font-medium">{j.title}</div>
                <div className="text-sm text-slate-400">
                  {j.company} · {j.location}
                </div>
              </div>
              <div className="text-right text-xs">
                <div className="px-2 py-0.5 rounded bg-slate-800 inline-block capitalize">
                  {j.seniority}
                </div>
                {j.salary_min && j.salary_max && (
                  <div className="text-emerald-400 mt-1">
                    ${Math.round(j.salary_min / 1000)}k – ${Math.round(j.salary_max / 1000)}k
                  </div>
                )}
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {j.skills.slice(0, 8).map((s) => (
                <span
                  key={s.id}
                  className="text-xs px-2 py-0.5 rounded bg-brand-600/10 text-brand-400 border border-brand-600/20"
                >
                  {s.name}
                </span>
              ))}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
