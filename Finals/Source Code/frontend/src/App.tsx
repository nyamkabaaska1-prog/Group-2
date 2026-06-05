import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import Skills from "./pages/Skills";
import Trends from "./pages/Trends";
import SalaryPredictor from "./pages/SalaryPredictor";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="skills" element={<Skills />} />
        <Route path="trends" element={<Trends />} />
        <Route path="predict" element={<SalaryPredictor />} />
      </Route>
    </Routes>
  );
}
