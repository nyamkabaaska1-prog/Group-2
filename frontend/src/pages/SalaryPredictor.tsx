import { useEffect, useState } from "react";
import { api, PredictResponse, SkillDemand } from "../api";

export default function SalaryPredictor() {
  const [title, setTitle] = useState("Senior Machine Learning Engineer");
  const [isRemote, setIsRemote] = useState(true);
  const [allSkills, setAllSkills] = useState<SkillDemand[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set(["Python", "PyTorch", "AWS"]));
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.skillsDemand(40).then(setAllSkills).catch(console.error);
  }, []);

  const toggle = (s: string) => {
    const next = new Set(selected);
    if (next.has(s)) next.delete(s);
    else next.add(s);
    setSelected(next);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.predictSalary({
        title,
        is_remote: isRemote,
        skills: Array.from(selected),
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Salary Predictor</h1>
      <p className="text-sm text-slate-400">
        Fill in a role; the model infers seniority from the title and predicts the midpoint salary
        using the gradient-boosted regressor trained on real Remotive postings with parsed pay
        ranges.
      </p>

      <form onSubmit={submit} className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-5">
        <div>
          <label className="text-xs uppercase tracking-wide text-slate-400">Job title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
          />
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isRemote}
            onChange={(e) => setIsRemote(e.target.checked)}
            className="accent-brand-500"
          />
          Remote role
        </label>

        <div>
          <label className="text-xs uppercase tracking-wide text-slate-400">
            Skills ({selected.size} selected)
          </label>
          <div className="mt-2 flex flex-wrap gap-2 max-h-56 overflow-y-auto">
            {allSkills.map((s) => {
              const on = selected.has(s.skill);
              return (
                <button
                  type="button"
                  key={s.skill}
                  onClick={() => toggle(s.skill)}
                  className={`px-3 py-1 text-xs rounded-full border ${
                    on
                      ? "bg-brand-600 border-brand-500 text-white"
                      : "bg-slate-950 border-slate-800 text-slate-300 hover:border-brand-500/50"
                  }`}
                >
                  {s.skill}
                </button>
              );
            })}
          </div>
        </div>

        <button
          disabled={loading}
          className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 px-5 py-2 rounded text-sm font-medium"
        >
          {loading ? "Predicting..." : "Predict salary"}
        </button>
      </form>

      {result && (
        <div className="bg-gradient-to-br from-brand-600/30 to-slate-900 border border-brand-500/30 rounded-lg p-6">
          <div className="text-xs uppercase tracking-wide text-brand-400">Predicted salary</div>
          <div className="text-4xl font-bold mt-1">
            ${Math.round(result.predicted_salary).toLocaleString()}
          </div>
          <div className="mt-3 flex gap-4 text-sm text-slate-300">
            <span>
              Seniority: <span className="font-medium capitalize">{result.seniority}</span>
            </span>
            <span>
              Confidence: <span className="font-medium capitalize">{result.confidence}</span>
            </span>
          </div>
          <ul className="mt-4 list-disc list-inside text-xs text-slate-400 space-y-0.5">
            {result.drivers.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
