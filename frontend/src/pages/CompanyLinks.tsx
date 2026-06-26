import { useState, useMemo } from "react";
import { COMPANIES } from "../data/companies";

const CATEGORIES = [...new Set(COMPANIES.map((c) => c.category))];

export default function CompanyLinks() {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let list = COMPANIES;
    if (activeCategory) {
      list = list.filter((c) => c.category === activeCategory);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) => c.name.toLowerCase().includes(q) || c.description.toLowerCase().includes(q)
      );
    }
    return list;
  }, [activeCategory, search]);

  return (
    <div className="page">
      <h1>🏢 大厂招聘直通车</h1>
      <p className="welcome">点击卡片直接跳转到各公司校招/社招官网，建议在新标签页打开</p>

      <div className="toolbar">
        <input
          className="search-input"
          type="text"
          placeholder="🔍 搜索公司名..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "20px", flexWrap: "wrap" }}>
        <button
          className={!activeCategory ? "btn-primary" : "btn"}
          style={{ fontSize: "13px", padding: "6px 14px" }}
          onClick={() => setActiveCategory(null)}
        >
          全部（{COMPANIES.length}）
        </button>
        {CATEGORIES.map((cat) => {
          const count = COMPANIES.filter((c) => c.category === cat).length;
          return (
            <button
              key={cat}
              className={activeCategory === cat ? "btn-primary" : "btn"}
              style={{ fontSize: "13px", padding: "6px 14px" }}
              onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
            >
              {cat}（{count}）
            </button>
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">🔍</div>
          <p>没有匹配的公司</p>
        </div>
      ) : (
        <div className="company-grid">
          {filtered.map((company) => (
            <div
              key={company.name}
              className="company-card"
              onClick={() => window.open(company.url, "_blank", "noopener,noreferrer")}
              role="link"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter") window.open(company.url, "_blank", "noopener,noreferrer");
              }}
            >
              <div className="company-card-header">
                <span className="company-name">{company.name}</span>
                <span className="company-category">{company.category}</span>
              </div>
              <p className="company-desc">{company.description}</p>
              <span className="company-link-hint">🔗 访问官网 →</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
