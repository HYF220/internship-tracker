import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { getJobs, deleteJob, updateJob } from "../api";
import type { Job } from "../api";
import Loading from "../components/Loading";
import Modal from "../components/Modal";

const STATUS_MAP: Record<string, string> = {
  saved: "已保存",
  applied: "已投递",
  interview: "面试中",
  offer: "已获 Offer",
  rejected: "已拒绝",
  withdrawn: "已撤回",
};

export default function JobsList() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // 删除确认弹窗
  const [deleteTarget, setDeleteTarget] = useState<Job | null>(null);

  // 编辑弹窗
  const [editTarget, setEditTarget] = useState<Job | null>(null);
  const [editForm, setEditForm] = useState({ company_name: "", title: "", location: "", salary_range: "", job_url: "", jd_text: "", status: "" });
  const [editSubmitting, setEditSubmitting] = useState(false);

  async function loadJobs() {
    setLoading(true);
    setError("");
    try {
      setJobs(await getJobs());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadJobs(); }, []);

  // 前端搜索过滤
  const filtered = useMemo(() => {
    if (!search.trim()) return jobs;
    const q = search.toLowerCase();
    return jobs.filter(
      (j) =>
        j.company_name.toLowerCase().includes(q) ||
        j.title.toLowerCase().includes(q)
    );
  }, [jobs, search]);

  // 打开编辑弹窗
  function openEdit(job: Job) {
    setEditTarget(job);
    setEditForm({
      company_name: job.company_name,
      title: job.title,
      location: job.location || "",
      salary_range: job.salary_range || "",
      job_url: job.job_url || "",
      jd_text: job.jd_text || "",
      status: job.status,
    });
  }

  async function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editTarget) return;
    setEditSubmitting(true);
    try {
      const data: Record<string, string> = {};
      for (const [k, v] of Object.entries(editForm)) {
        if (v) data[k] = v;
      }
      const updated = await updateJob(editTarget.id, data);
      setJobs(jobs.map((j) => (j.id === updated.id ? updated : j)));
      setEditTarget(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "更新失败");
    } finally {
      setEditSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await deleteJob(deleteTarget.id);
      setJobs(jobs.filter((j) => j.id !== deleteTarget.id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeleteTarget(null);
    }
  }

  if (loading) return <div className="page"><Loading /></div>;

  return (
    <div className="page">
      <h1>岗位列表</h1>

      <div className="toolbar">
        <input
          className="search-input"
          type="text"
          placeholder="🔍 搜索公司名或岗位名..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="row-count">共 {filtered.length} 个岗位</span>
        <Link to="/jobs/create" className="btn-primary">＋ 添加岗位</Link>
        <Link to="/dashboard" className="btn">← 工作台</Link>
      </div>

      {error && <p className="error">{error}</p>}

      {!error && jobs.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📭</div>
          <p>还没有岗位，<Link to="/jobs/create">创建一个吧</Link></p>
        </div>
      ) : !error && filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">🔍</div>
          <p>没有匹配 "{search}" 的岗位</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>公司</th>
                <th>岗位</th>
                <th>地点</th>
                <th>薪资</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((job) => (
                <tr key={job.id}>
                  <td>{job.company_name}</td>
                  <td>{job.title}</td>
                  <td>{job.location || "-"}</td>
                  <td>{job.salary_range || "-"}</td>
                  <td>
                    <span className={`tag tag-${job.status}`}>
                      {STATUS_MAP[job.status] || job.status}
                    </span>
                  </td>
                  <td>
                    <div className="col-actions">
                      <button className="btn-sm" onClick={() => openEdit(job)}>编辑</button>
                      <button className="btn-sm btn-danger" onClick={() => setDeleteTarget(job)}>删除</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 删除确认 Modal */}
      {deleteTarget && (
        <Modal title="确认删除" onClose={() => setDeleteTarget(null)}>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: 1.6 }}>
            确定要删除 <strong>{deleteTarget.company_name}</strong> - {deleteTarget.title} 吗？
            此操作不可撤销。
          </p>
          <div className="modal-actions">
            <button className="btn" onClick={() => setDeleteTarget(null)}>取消</button>
            <button className="btn-danger" onClick={handleDelete}>确认删除</button>
          </div>
        </Modal>
      )}

      {/* 编辑 Modal */}
      {editTarget && (
        <Modal title="编辑岗位" onClose={() => setEditTarget(null)}>
          <form onSubmit={handleEdit} className="form" style={{ padding: 0, border: "none", boxShadow: "none" }}>
            <div className="form-row">
              <label>公司名称<span className="required">*</span>
                <input value={editForm.company_name} onChange={(e) => setEditForm({ ...editForm, company_name: e.target.value })} required />
              </label>
              <label>岗位名称<span className="required">*</span>
                <input value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} required />
              </label>
            </div>
            <div className="form-row">
              <label>工作地点
                <input value={editForm.location} onChange={(e) => setEditForm({ ...editForm, location: e.target.value })} />
              </label>
              <label>薪资范围
                <input value={editForm.salary_range} onChange={(e) => setEditForm({ ...editForm, salary_range: e.target.value })} />
              </label>
            </div>
            <label>岗位链接
              <input value={editForm.job_url} onChange={(e) => setEditForm({ ...editForm, job_url: e.target.value })} />
            </label>
            <label>状态
              <select value={editForm.status} onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}>
                {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <label>岗位描述
              <textarea value={editForm.jd_text} onChange={(e) => setEditForm({ ...editForm, jd_text: e.target.value })} rows={3} />
            </label>
            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setEditTarget(null)}>取消</button>
              <button type="submit" className="btn-primary" disabled={editSubmitting}>
                {editSubmitting ? <><span className="spinner" /> 保存中...</> : "保存"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
