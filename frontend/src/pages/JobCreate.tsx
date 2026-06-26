import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { createJob } from "../api";

export default function JobCreate() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    company_name: "",
    title: "",
    location: "",
    job_url: "",
    jd_text: "",
    salary_range: "",
    status: "saved",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data: Record<string, string> = {};
      for (const [key, value] of Object.entries(form)) {
        if (value) data[key] = value;
      }
      await createJob(data as unknown as { company_name: string; title: string });
      navigate("/jobs");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>添加新岗位</h1>
      <div className="toolbar">
        <Link to="/jobs" className="btn">← 返回列表</Link>
      </div>

      <form onSubmit={handleSubmit} className="form">
        {error && <p className="error">{error}</p>}

        <div className="form-row">
          <label>
            公司名称<span className="required">*</span>
            <input name="company_name" value={form.company_name} onChange={handleChange} required />
          </label>
          <label>
            岗位名称<span className="required">*</span>
            <input name="title" value={form.title} onChange={handleChange} required />
          </label>
        </div>

        <div className="form-row">
          <label>
            工作地点
            <input name="location" value={form.location} onChange={handleChange} />
          </label>
          <label>
            薪资范围
            <input name="salary_range" value={form.salary_range} onChange={handleChange} placeholder="如：15k-25k" />
          </label>
        </div>

        <label>
          岗位链接
          <input name="job_url" value={form.job_url} onChange={handleChange} placeholder="https://..." />
        </label>

        <label>
          状态
          <select name="status" value={form.status} onChange={handleChange}>
            <option value="saved">已保存</option>
            <option value="applied">已投递</option>
            <option value="interview">面试中</option>
            <option value="offer">已获 Offer</option>
            <option value="rejected">已拒绝</option>
            <option value="withdrawn">已撤回</option>
          </select>
        </label>

        <label>
          岗位描述
          <textarea name="jd_text" value={form.jd_text} onChange={handleChange} rows={4} />
        </label>

        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? <><span className="spinner" /> 创建中...</> : "创建岗位"}
        </button>
      </form>
    </div>
  );
}
