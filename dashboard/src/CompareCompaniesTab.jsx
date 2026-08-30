import React, { useState, useEffect } from "react";
import { API_BASE as API } from "./config";

async function apiGet(path) {
  const r = await fetch(API + path);
  return r.json();
}

function Card({ children, style = {} }) {
  return (
    <div style={{
      background:"#16162a", border:"1px solid #232343",
      borderRadius:14, padding:"24px",
      boxShadow:"0 4px 24px rgba(0,0,0,0.25)", ...style
    }}>{children}</div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{
      color:"#a4a4d0", fontSize:11, fontWeight:700,
      letterSpacing:"0.1em", textTransform:"uppercase", marginBottom:18
    }}>{children}</div>
  );
}

const COLORS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b"];

export default function CompareCompaniesTab() {
  const [allCompanies, setAllCompanies] = useState([]);
  const [selected, setSelected]         = useState([]);
  const [compareData, setCompareData]   = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState("");

  useEffect(() => {
    apiGet("/api/companies")
      .then(d => setAllCompanies(d.companies || []))
      .catch(() => {});
  }, []);

  const toggleSelect = (name) => {
    setSelected(prev => {
      if (prev.includes(name)) return prev.filter(n => n !== name);
      if (prev.length >= 4) return prev; // max 4
      return [...prev, name];
    });
  };

  const runCompare = async () => {
    if (selected.length < 2) {
      setError("Select at least 2 companies to compare.");
      return;
    }
    setError("");
    setLoading(true);
    setCompareData(null);
    try {
      const names = selected.map(encodeURIComponent).join(",");
      const d = await apiGet(`/api/compare-companies?names=${names}`);
      if (d.error) {
        setError(d.error);
      } else {
        setCompareData(d.companies || []);
      }
    } catch {
      setError("Failed to compare. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:24 }}>

      <Card>
        <SectionTitle>Select Companies to Compare (2–4)</SectionTitle>

        {!allCompanies.length ? (
          <div style={{ color:"#6b6b9a", fontSize:13 }}>
            No companies analysed yet. Go to "Analyze Competitor" and run an analysis first.
          </div>
        ) : (
          <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
            {allCompanies.map(c => {
              const isSelected = selected.includes(c.name);
              return (
                <button
                  key={c.name}
                  onClick={() => toggleSelect(c.name)}
                  style={{
                    background: isSelected ? "#6366f1" : "#0f0f23",
                    border: `1px solid ${isSelected ? "#6366f1" : "#232343"}`,
                    borderRadius: 10, color: isSelected ? "#fff" : "#d2d2f0",
                    padding: "10px 18px", fontSize: 13, fontWeight: 500,
                    cursor: "pointer"
                  }}
                >
                  {c.name}
                  <span style={{
                    marginLeft: 8, fontSize: 11,
                    color: isSelected ? "#e0e0ff" : "#6b6b9a"
                  }}>
                    {c.articles_found || 0} articles
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {error && (
          <div style={{ color:"#ef4444", fontSize:13, marginTop:14 }}>{error}</div>
        )}

        <button
          onClick={runCompare}
          disabled={loading || selected.length < 2}
          style={{
            marginTop: 18,
            background: (loading || selected.length < 2) ? "#1d1d36"
              : "linear-gradient(135deg,#6366f1,#8b5cf6)",
            border: "none", borderRadius: 10, color: "#fff",
            padding: "12px 24px", fontSize: 14, fontWeight: 600,
            cursor: (loading || selected.length < 2) ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Comparing..." : `Compare ${selected.length ? `(${selected.length})` : ""}`}
        </button>
      </Card>

      {compareData && (
        <div style={{
          display: "grid",
          gridTemplateColumns: `repeat(${compareData.length}, 1fr)`,
          gap: 20
        }}>
          {compareData.map((c, i) => {
            const color = COLORS[i % COLORS.length];

            if (!c.found) {
              return (
                <Card key={c.company} style={{ borderTop: `3px solid ${color}` }}>
                  <div style={{ color: "#ef4444", fontSize: 13 }}>
                    {c.company} — no data found.
                  </div>
                </Card>
              );
            }

            return (
              <Card key={c.company} style={{ borderTop: `3px solid ${color}` }}>
                <div style={{ color, fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
                  {c.company}
                </div>
                <a href={c.website} target="_blank" rel="noreferrer" style={{
                  color: "#6b6b9a", fontSize: 12, textDecoration: "none",
                  display: "block", marginBottom: 16
                }}>
                  {c.website}
                </a>

                <div style={{ display:"flex", justifyContent:"space-between", marginBottom: 16 }}>
                  <div>
                    <div style={{ color:"#6b6b9a", fontSize:10, textTransform:"uppercase" }}>Articles</div>
                    <div style={{ color:"#d2d2f0", fontSize:20, fontWeight:700 }}>{c.article_count}</div>
                  </div>
                  <div>
                    <div style={{ color:"#6b6b9a", fontSize:10, textTransform:"uppercase" }}>Last Scraped</div>
                    <div style={{ color:"#d2d2f0", fontSize:11, marginTop:4 }}>
                      {c.last_scraped ? c.last_scraped.split(" ")[0] : "—"}
                    </div>
                  </div>
                </div>

                {c.description && (
                  <p style={{ color:"#cbd5e1", fontSize:12, lineHeight:1.6, marginBottom:16 }}>
                    {c.description}
                  </p>
                )}

                <div style={{ color:"#a4a4d0", fontSize:11, fontWeight:700,
                  textTransform:"uppercase", marginBottom:10 }}>Top Topics</div>
                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  {c.top_topics.length ? c.top_topics.map(t => (
                    <div key={t.topic} style={{ display:"flex",
                      justifyContent:"space-between", alignItems:"center" }}>
                      <span style={{ color:"#d2d2f0", fontSize:12 }}>{t.topic}</span>
                      <span style={{
                        background: `${color}15`, color, border: `1px solid ${color}35`,
                        borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 700
                      }}>{t.count}</span>
                    </div>
                  )) : (
                    <div style={{ color:"#6b6b9a", fontSize:12 }}>No topic data.</div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}