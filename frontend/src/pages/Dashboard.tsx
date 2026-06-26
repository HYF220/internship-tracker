import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, getMe } from "../api";
import type { Stats, User } from "../api";
import Loading from "../components/Loading";

const STAT_CARDS = [
  { key: "total_jobs", label: "岗位总数", icon: "📋", cls: "jobs" },
  { key: "total_applied", label: "已投递", icon: "📨", cls: "applied" },
  { key: "total_interview", label: "面试中", icon: "💬", cls: "interview" },
  { key: "total_offer", label: "Offer", icon: "🏆", cls: "offer" },
  { key: "total_rejected", label: "已拒绝", icon: "❌", cls: "rejected" },
] as const;

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [userData, statsData] = await Promise.all([getMe(), getStats()]);
        setUser(userData);
        setStats(statsData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "加载失败");
      }
    }
    load();
  }, []);

  if (error) return <div className="page"><p className="error">{error}</p></div>;
  if (!stats || !user) return <div className="page"><Loading /></div>;

  const allZero = Object.values(stats).every((v) => v === 0);

  return (
    <div className="page">
      <h1>工作台</h1>
      <p className="welcome">👋 欢迎，{user.email}</p>

      <div className="stats-grid">
        {STAT_CARDS.map(({ key, label, icon, cls }) => (
          <div key={key} className={`stat-card ${cls}`}>
            <div className="stat-icon">{icon}</div>
            <span className="stat-number">{stats[key as keyof Stats]}</span>
            <span className="stat-label">{label}</span>
          </div>
        ))}
      </div>

      {allZero && (
        <div className="empty">
          <div className="empty-icon">🚀</div>
          <p>还没有数据，<Link to="/jobs/create">添加你的第一个岗位</Link> 开始投递之旅吧！</p>
        </div>
      )}

      <div className="actions">
        <Link to="/jobs" className="btn">📄 查看岗位列表</Link>
        <Link to="/jobs/create" className="btn-primary">＋ 添加新岗位</Link>
      </div>
    </div>
  );
}
