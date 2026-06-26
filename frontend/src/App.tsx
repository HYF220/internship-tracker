import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate, useLocation } from "react-router-dom";
import { isLoggedIn, clearToken } from "./api";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import JobsList from "./pages/JobsList";
import JobCreate from "./pages/JobCreate";
import CompanyLinks from "./pages/CompanyLinks";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();

  if (!isLoggedIn()) return null;

  const isActive = (path: string) => location.pathname === path ? "active" : "";

  return (
    <nav className="navbar">
      <span className="navbar-brand">📋 实习投递管理系统</span>
      <div className="nav-links">
        <Link to="/dashboard" className={isActive("/dashboard")}>工作台</Link>
        <Link to="/jobs" className={isActive("/jobs")}>岗位列表</Link>
        <Link to="/jobs/create" className={isActive("/jobs/create")}>添加岗位</Link>
        <Link to="/companies" className={isActive("/companies")}>大厂直通车</Link>
      </div>
      <button onClick={() => { clearToken(); navigate("/login"); }} className="btn-sm btn-danger">退出</button>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/jobs" element={<ProtectedRoute><JobsList /></ProtectedRoute>} />
        <Route path="/jobs/create" element={<ProtectedRoute><JobCreate /></ProtectedRoute>} />
        <Route path="/companies" element={<ProtectedRoute><CompanyLinks /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
