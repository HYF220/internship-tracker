import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-center">
      <div className="form-card">
        <div className="auth-brand">
          <h1>📋 实习投递管理系统</h1>
          <p>登录您的账号</p>
        </div>
        <form onSubmit={handleSubmit} className="form">
          {error && <p className="error">{error}</p>}
          <label>
            邮箱
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? <><span className="spinner" /> 登录中...</> : "登录"}
          </button>
        </form>
        <p className="link">
          还没有账号？<Link to="/register">去注册</Link>
        </p>
      </div>
    </div>
  );
}
