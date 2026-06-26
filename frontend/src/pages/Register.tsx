import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../api";

export default function Register() {
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
      await register(email, password);
      navigate("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-center">
      <div className="form-card">
        <div className="auth-brand">
          <h1>📋 实习投递管理系统</h1>
          <p>创建新账号</p>
        </div>
        <form onSubmit={handleSubmit} className="form">
          {error && <p className="error">{error}</p>}
          <label>
            邮箱
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            密码<span className="required">*</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
          </label>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? <><span className="spinner" /> 注册中...</> : "注册"}
          </button>
        </form>
        <p className="link">
          已有账号？<Link to="/login">去登录</Link>
        </p>
      </div>
    </div>
  );
}
