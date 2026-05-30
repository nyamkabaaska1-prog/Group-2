import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/jobs", label: "Jobs" },
  { to: "/skills", label: "Skills" },
  { to: "/trends", label: "Trends" },
  { to: "/predict", label: "Salary Predictor" },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 border-r border-slate-800 px-4 py-6 hidden md:block">
        <div className="text-lg font-semibold mb-8">
          <span className="text-brand-400">AI</span> Job Market
        </div>
        <nav className="space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `block px-3 py-2 rounded text-sm ${
                  isActive
                    ? "bg-brand-600/20 text-brand-400"
                    : "text-slate-300 hover:bg-slate-800/60"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 px-6 py-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
