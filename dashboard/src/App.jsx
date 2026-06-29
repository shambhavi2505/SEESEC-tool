import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell
} from "recharts";

const API = "http://localhost:8000";
const COLORS = ["#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b","#ef4444","#ec4899"];
const COMP_COLORS = {
  AuthBridge:"#6366f1", IDfy:"#8b5cf6", Signzy:"#06b6d4",
  HyperVerge:"#10b981", Bureau:"#f59e0b", DigiTap:"#ef4444"
};

async function api(path) {
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

function StatPill({ label, value, color, sub }) {
  return (
    <div style={{
      background:"#0f0f23", border:`1px solid ${color}20`,
      borderRadius:12, padding:"20px 24px", flex:"1 1 180px",
      borderTop:`3px solid ${color}`
    }}>
      <div style={{ color:"#7e7eb2", fontSize:11, fontWeight:600,
        textTransform:"uppercase", letterSpacing:"0.08em", marginBottom:8 }}>{label}</div>
      <div style={{ color, fontSize:26, fontWeight:700, letterSpacing:"-0.02em" }}>{value}</div>
      {sub && <div style={{ color:"#5a5a88", fontSize:11, marginTop:4 }}>{sub}</div>}
    </div>
  );
}

function Badge({ text, color="#6366f1" }) {
  return (
    <span style={{
      background:`${color}15`, color, border:`1px solid ${color}35`,
      borderRadius:6, padding:"3px 10px", fontSize:11, fontWeight:600
    }}>{text}</span>
  );
}

function KwBar({ label, count, max, color }) {
  const pct = Math.max((count / max) * 100, 2);
  return (
    <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:10 }}>
      <span style={{ color:"#d2d2f0", fontSize:12, width:155, flexShrink:0,
        overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{label}</span>
      <div style={{ flex:1, height:7, background:"#0f0f23", borderRadius:4, overflow:"hidden" }}>
        <div style={{ width:`${pct}%`, height:"100%",
          background:`linear-gradient(90deg,${color},${color}99)`, borderRadius:4 }}/>
      </div>
      <span style={{ color, fontWeight:700, fontSize:12, width:30, textAlign:"right" }}>{count}</span>
    </div>
  );
}

function ImpactDot({ level }) {
  const c = level==="High" ? "#ef4444" : level==="Medium" ? "#f59e0b" : "#10b981";
  return <span style={{ display:"inline-block", width:8, height:8,
    borderRadius:"50%", background:c, marginRight:6, verticalAlign:"middle" }}/>;
}


function OverviewTab({ stats, topics }) {
  if (!stats) return (
    <div style={{ color:"#8a8ab6", padding:80, textAlign:"center", fontSize:14 }}>
      Loading dashboard...
    </div>
  );

  const compData = stats.competitor_counts || [];
  const kwData   = (topics?.top_keywords || []).slice(0,12);
  const bgData   = (topics?.top_bigrams  || []).slice(0,10);
  const maxKw    = kwData[0]?.count || 1;

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:24 }}>

      {/* Stat pills */}
      <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
        <StatPill label="Total Articles Tracked" value={stats.total_articles}
          sub="across all competitors" color="#6366f1"/>
        <StatPill label="Competitors Monitored" value={compData.length}
          sub="active sources" color="#06b6d4"/>
        <StatPill label="Most Active Publisher"
          value={compData[0]?.competitor || "—"}
          sub={`${compData[0]?.count || 0} articles`} color="#10b981"/>
        <StatPill label="Least Active Publisher"
          value={compData[compData.length-1]?.competitor || "—"}
          sub={`${compData[compData.length-1]?.count || 0} articles`} color="#f59e0b"/>
      </div>

      {/* Charts row */}
      <div style={{ display:"grid", gridTemplateColumns:"3fr 2fr", gap:24 }}>
        <Card>
          <SectionTitle>Publishing Volume by Competitor</SectionTitle>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={compData} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e38" vertical={false}/>
              <XAxis dataKey="competitor" tick={{ fill:"#7e7eb2", fontSize:11 }}
                axisLine={false} tickLine={false}/>
              <YAxis tick={{ fill:"#7e7eb2", fontSize:11 }} axisLine={false} tickLine={false}/>
              <Tooltip contentStyle={{ background:"#0f0f23", border:"1px solid #232343",
                borderRadius:8 }} labelStyle={{ color:"#d2d2f0", fontWeight:600 }}
                itemStyle={{ color:"#6366f1" }}/>
              <Bar dataKey="count" radius={[6,6,0,0]}>
                {compData.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <SectionTitle>Top Keywords</SectionTitle>
          {kwData.map(({word,count}) => (
            <KwBar key={word} label={word} count={count} max={maxKw} color="#6366f1"/>
          ))}
        </Card>
      </div>

      {/* Bigrams */}
      <Card>
        <SectionTitle>Top Keyword Phrases (Bigrams)</SectionTitle>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",
          gap:"8px 40px", marginTop:8 }}>
          {bgData.map(({bigram,count}) => (
            <KwBar key={bigram} label={bigram} count={count}
              max={bgData[0]?.count||1} color="#8b5cf6"/>
          ))}
        </div>
      </Card>

    </div>
  );
}


function ContentTab({ competitors }) {
  const [items, setItems]     = useState([]);
  const [total, setTotal]     = useState(0);
  const [filterComp, setComp] = useState("All");
  const [search, setSearch]   = useState("");
  const [page, setPage]       = useState(0);

  const load = useCallback(async () => {
    const comp = filterComp==="All" ? "" : `&competitor=${filterComp}`;
    const d = await api(`/api/content?limit=80&offset=${page*80}${comp}`);
    setItems(d.items||[]);
    setTotal(d.total||0);
  }, [filterComp, page]);

  useEffect(() => { load(); }, [load]);
  const filtered = items.filter(i =>
    i.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {/* Filters */}
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap", alignItems:"center" }}>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search article titles..."
          style={{ flex:1, minWidth:240, background:"#16162a",
            border:"1px solid #232343", borderRadius:10, color:"#d2d2f0",
            padding:"10px 16px", fontSize:13, outline:"none" }}
          onFocus={e => e.target.style.borderColor="#6366f1"}
          onBlur={e => e.target.style.borderColor="#232343"}/>
        <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
          {["All",...(competitors||[])].map(c => (
            <button key={c} onClick={() => { setComp(c); setPage(0); }}
              style={{ background: filterComp===c ? "#6366f1":"#16162a",
                border:`1px solid ${filterComp===c ? "#6366f1":"#232343"}`,
                borderRadius:8, color: filterComp===c ? "#fff":"#7e7eb2",
                padding:"7px 14px", fontSize:12, fontWeight:500, cursor:"pointer" }}>{c}</button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{ background:"#16162a", borderRadius:14, border:"1px solid #232343",
        overflow:"hidden", boxShadow:"0 4px 24px rgba(0,0,0,0.2)" }}>
        <div style={{ display:"grid", gridTemplateColumns:"145px 1fr 130px 115px",
          background:"#0f0f23", padding:"12px 24px", color:"#6b6b9a",
          fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase",
          borderBottom:"1px solid #232343" }}>
          <span>Competitor</span><span>Title</span><span>Type</span><span>Date</span>
        </div>
        {filtered.map((item, i) => (
          <div key={item.id} style={{ display:"grid",
            gridTemplateColumns:"145px 1fr 130px 115px",
            padding:"13px 24px", borderBottom:"1px solid #1e1e38",
            background: i%2===0 ? "#16162a":"#131326",
            alignItems:"center", gap:12 }}>
            <span style={{ color:COMP_COLORS[item.competitor_name]||"#6366f1",
              fontWeight:700, fontSize:12 }}>{item.competitor_name}</span>
            <a href={item.url} target="_blank" rel="noreferrer"
              style={{ color:"#d2d2f0", fontSize:13, textDecoration:"none",
                lineHeight:1.5, fontWeight:400 }}
              onMouseEnter={e => e.target.style.color="#6366f1"}
              onMouseLeave={e => e.target.style.color="#d2d2f0"}>{item.title}</a>
            <Badge text={item.content_type}
              color={item.content_type==="Case Study" ? "#10b981"
                : item.content_type==="Whitepaper" ? "#f59e0b" : "#06b6d4"}/>
            <span style={{ color:"#6b6b9a", fontSize:12 }}>{item.published_date||"—"}</span>
          </div>
        ))}
        {!filtered.length && (
          <div style={{ padding:60, textAlign:"center", color:"#6b6b9a", fontSize:14 }}>
            No articles match your filter.
          </div>
        )}
      </div>

      {/* Pagination */}
      <div style={{ display:"flex", justifyContent:"space-between",
        alignItems:"center", color:"#6b6b9a", fontSize:12, marginTop:14 }}>
        <span>Showing <b style={{ color:"#d2d2f0" }}>{filtered.length}</b> of <b style={{ color:"#d2d2f0" }}>{total}</b> articles</span>
        {total > 80 && (
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <button onClick={() => setPage(p => Math.max(0,p-1))} disabled={page===0}
              style={{ background:"#232343", border:"none", color:"#d2d2f0",
                borderRadius:6, padding:"5px 14px", cursor:"pointer",
                opacity: page===0 ? 0.4:1 }}>← Prev</button>
            <span style={{ color:"#d2d2f0" }}>Page {page+1}</span>
            <button onClick={() => setPage(p => p+1)}
              disabled={(page+1)*80 >= total}
              style={{ background:"#232343", border:"none", color:"#d2d2f0",
                borderRadius:6, padding:"5px 14px", cursor:"pointer",
                opacity:(page+1)*80>=total ? 0.4:1 }}>Next →</button>
          </div>
        )}
      </div>
    </div>
  );
}


function OpportunitiesTab() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/api/opportunities").then(d => { setData(d); setLoading(false); });
  }, []);

  if (loading) return (
    <div style={{ color:"#8a8ab6", padding:80, textAlign:"center" }}>
      Loading intelligence pipeline...
    </div>
  );

  const gaps    = data?.gap_analyses || [];
  const recs    = data?.recommendations || [];
  const rawGaps = data?.gaps || [];
  const summary = data?.executive_summary || "";
  const impColor = { CRITICAL:"#ef4444", HIGH:"#f59e0b", MEDIUM:"#06b6d4" };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:24 }}>

      {/* Executive Summary */}
      {summary && (
        <Card style={{ borderLeft:"4px solid #6366f1",
          background:"linear-gradient(135deg,#1a1a35,#16162a)" }}>
          <SectionTitle>Executive Intelligence Summary</SectionTitle>
          <p style={{ color:"#d2d2f0", lineHeight:1.8, fontSize:14, margin:0 }}>{summary}</p>
        </Card>
      )}

      {/* Gap Score Bar Chart */}
      {rawGaps.length > 0 && (
        <Card>
          <SectionTitle>Content Gap Scores — Ranked by Opportunity</SectionTitle>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={rawGaps.slice(0,10).map(g => ({ topic:g.topic, score:g.gap_score }))}
              layout="vertical" barSize={16} margin={{ left:20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e38" horizontal={false}/>
              <XAxis type="number" tick={{ fill:"#7e7eb2", fontSize:11 }}
                axisLine={false} tickLine={false}/>
              <YAxis type="category" dataKey="topic" width={140}
                tick={{ fill:"#d2d2f0", fontSize:11 }} axisLine={false} tickLine={false}/>
              <Tooltip contentStyle={{ background:"#0f0f23", border:"1px solid #232343",
                borderRadius:8 }} labelStyle={{ color:"#d2d2f0" }}
                itemStyle={{ color:"#6366f1" }}/>
              <Bar dataKey="score" radius={[0,6,6,0]}>
                {rawGaps.slice(0,10).map((_,i) => (
                  <Cell key={i} fill={COLORS[i%COLORS.length]}/>
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ color:"#6b6b9a", fontSize:11, marginTop:8 }}>
            Higher score = more competitors covering it + higher strategic importance + lower current coverage
          </div>
        </Card>
      )}

      {!gaps.length && !recs.length && (
        <Card style={{ textAlign:"center", padding:48 }}>
          <div style={{ color:"#8a8ab6", fontSize:14, lineHeight:1.7 }}>
            No AI insights generated yet.<br/>
            <code style={{ background:"#0f0f23", padding:"4px 10px",
              borderRadius:6, color:"#f59e0b", fontSize:12 }}>
              python analysis/ai.py
            </code>
          </div>
        </Card>
      )}

      {/* Gap Analyses */}
      {gaps.length > 0 && (
        <div>
          <div style={{ color:"#d2d2f0", fontWeight:700, fontSize:15, marginBottom:14 }}>
            Content Gap Analysis
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            {gaps.map((g, i) => {
              const color = impColor[g.strategic_importance] || "#6366f1";
              return (
                <Card key={i} style={{ borderLeft:`4px solid ${color}` }}>
                  <div style={{ display:"flex", justifyContent:"space-between",
                    alignItems:"center", marginBottom:10 }}>
                    <div style={{ color, fontWeight:700, fontSize:15 }}>{g.topic}</div>
                    <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                      <span style={{ color:"#6b6b9a", fontSize:11 }}>
                        Gap Score: <b style={{ color:"#d2d2f0" }}>{g.gap_score}</b>
                      </span>
                      <Badge text={g.strategic_importance} color={color}/>
                    </div>
                  </div>
                  <p style={{ color:"#cbd5e1", fontSize:13, lineHeight:1.7,
                    marginBottom:12, marginTop:0 }}>{g.seesec_opportunity}</p>
                  <div style={{ color:"#6b6b9a", fontSize:12, marginBottom:14 }}>
                    Target: <span style={{ color:"#d2d2f0" }}>{g.target_audience}</span>
                  </div>
                  <div style={{ background:"#0f0f23", borderRadius:10,
                    padding:"14px 18px", border:"1px solid #232343" }}>
                    <div style={{ color:"#6b6b9a", fontSize:10, fontWeight:700,
                      textTransform:"uppercase", letterSpacing:"0.1em", marginBottom:10 }}>
                      SEO Title Ideas
                    </div>
                    {(g.seo_titles||[]).map((t,j) => (
                      <div key={j} style={{ color:"#10b981", fontSize:13,
                        fontWeight:500, marginBottom:6, paddingLeft:4,
                        borderLeft:"2px solid #10b98133", paddingLeft:10 }}>
                        {t}
                      </div>
                    ))}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recs.length > 0 && (
        <div>
          <div style={{ color:"#d2d2f0", fontWeight:700, fontSize:15,
            marginBottom:14, marginTop:8 }}>
            AI Content Recommendations for SEESEC
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            {recs.map((r, i) => (
              <Card key={i} style={{ borderLeft:"4px solid #10b981" }}>
                <div style={{ display:"flex", gap:14, alignItems:"flex-start", marginBottom:10 }}>
                  <div style={{ background: r.estimated_impact==="High"?"#ef444415":"#f59e0b15",
                    border:`1px solid ${r.estimated_impact==="High"?"#ef4444":"#f59e0b"}30`,
                    borderRadius:8, padding:"6px 10px", flexShrink:0 }}>
                    <ImpactDot level={r.estimated_impact}/>
                    <span style={{ color: r.estimated_impact==="High"?"#ef4444":"#f59e0b",
                      fontSize:10, fontWeight:700, textTransform:"uppercase",
                      letterSpacing:"0.08em" }}>{r.estimated_impact}</span>
                  </div>
                  <div style={{ flex:1 }}>
                    <div style={{ color:"#e2e2f8", fontWeight:600, fontSize:14,
                      lineHeight:1.4 }}>{r.title}</div>
                    <div style={{ color:"#6b6b9a", fontSize:11, marginTop:5 }}>
                      {r.content_type} &nbsp;·&nbsp;
                      Keyword: <span style={{ color:"#06b6d4", fontWeight:500 }}>
                        {r.target_keyword}
                      </span>
                    </div>
                  </div>
                </div>
                <p style={{ color:"#cbd5e1", fontSize:13, lineHeight:1.7,
                  marginBottom:12, marginTop:0 }}>{r.why_now}</p>
                {r.outline?.length > 0 && (
                  <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                    {r.outline.map((s,j) => (
                      <span key={j} style={{ background:"#0f0f23", color:"#7e7eb2",
                        border:"1px solid #232343", borderRadius:6,
                        padding:"3px 10px", fontSize:11 }}>
                        {j+1}. {s}
                      </span>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function CompareTab({ topics, stats }) {
  if (!topics || !stats) return (
    <div style={{ color:"#8a8ab6", padding:80, textAlign:"center" }}>
      Loading competitor matrix...
    </div>
  );

  const compKw = topics.competitor_keywords || {};
  const comps  = Object.keys(compKw);

  if (!comps.length) return (
    <Card>
      <div style={{ color:"#6b6b9a", fontSize:13 }}>No keyword data available.</div>
    </Card>
  );

  const allKw = {};
  comps.forEach(c => (compKw[c]||[]).forEach(({word,count}) => {
    allKw[word] = (allKw[word]||0) + count;
  }));
  const topWords = Object.entries(allKw).sort((a,b)=>b[1]-a[1])
    .slice(0,10).map(([w])=>w);

  const chartData = topWords.map(word => {
    const row = { keyword:word };
    comps.forEach(c => {
      const m = (compKw[c]||[]).find(k=>k.word===word);
      row[c] = m ? m.count : 0;
    });
    return row;
  });

  const maxVal = Math.max(...chartData.flatMap(row =>
    comps.map(c => row[c]||0)
  ));

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:24 }}>

      {/* Grouped bar chart */}
      <Card>
        <SectionTitle>Keyword Frequency — Competitor Comparison</SectionTitle>
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={chartData}
            margin={{ top:10, right:10, left:0, bottom:60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e38" vertical={false}/>
            <XAxis dataKey="keyword" angle={-35} textAnchor="end" height={80}
              tick={{ fill:"#7e7eb2", fontSize:11 }} axisLine={false} tickLine={false}/>
            <YAxis tick={{ fill:"#7e7eb2", fontSize:11 }} axisLine={false} tickLine={false}/>
            <Tooltip contentStyle={{ background:"#0f0f23", border:"1px solid #232343",
              borderRadius:8 }} labelStyle={{ color:"#d2d2f0" }}/>
            <Legend wrapperStyle={{ paddingTop:20, fontSize:12, color:"#7e7eb2" }}/>
            {comps.map((c,i) => (
              <Bar key={c} dataKey={c} fill={COLORS[i%COLORS.length]}
                radius={[3,3,0,0]} barSize={10}/>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Heatmap */}
      <Card>
        <SectionTitle>Keyword Focus Heatmap</SectionTitle>
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", minWidth:600 }}>
            <thead>
              <tr style={{ background:"#0f0f23" }}>
                <th style={{ textAlign:"left", padding:"10px 16px",
                  color:"#6b6b9a", fontSize:11, fontWeight:700,
                  letterSpacing:"0.08em", borderBottom:"1px solid #232343" }}>
                  KEYWORD
                </th>
                {comps.map((comp,i) => (
                  <th key={comp} style={{ padding:"10px 16px", textAlign:"center",
                    color:COLORS[i%COLORS.length], fontSize:11, fontWeight:700,
                    borderBottom:"1px solid #232343" }}>{comp}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {chartData.map((row,ri) => (
                <tr key={row.keyword}
                  style={{ background: ri%2===0?"#16162a":"#131326" }}>
                  <td style={{ padding:"10px 16px", color:"#e2e2f8",
                    fontWeight:600, fontSize:13, borderBottom:"1px solid #1e1e38" }}>
                    {row.keyword}
                  </td>
                  {comps.map((comp,i) => {
                    const val = row[comp]||0;
                    const intensity = maxVal>0 ? val/maxVal : 0;
                    return (
                      <td key={comp} style={{ padding:"10px 16px", textAlign:"center",
                        fontWeight:700, fontSize:13,
                        color: intensity>0.5 ? "#fff":"#a0a0c8",
                        borderBottom:"1px solid #1e1e38",
                        background:`rgba(99,102,241,${0.04+intensity*0.82})` }}>
                        {val || "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Per-competitor cards */}
      <div style={{ display:"grid",
        gridTemplateColumns:"repeat(auto-fill,minmax(210px,1fr))", gap:16 }}>
        {comps.map((comp,i) => (
          <Card key={comp} style={{ borderTop:`3px solid ${COLORS[i%COLORS.length]}`,
            padding:"18px 20px" }}>
            <div style={{ color:COLORS[i%COLORS.length], fontWeight:700,
              fontSize:14, marginBottom:14 }}>{comp}</div>
            {(compKw[comp]||[]).slice(0,8).map(({word,count}) => (
              <div key={word} style={{ display:"flex",
                justifyContent:"space-between", marginBottom:7 }}>
                <span style={{ color:"#b0b0d8", fontSize:12 }}>{word}</span>
                <span style={{ color:COLORS[i%COLORS.length],
                  fontWeight:700, fontSize:12 }}>{count}</span>
              </div>
            ))}
          </Card>
        ))}
      </div>
    </div>
  );
}


const TABS = ["Overview","Content Feed","Opportunities","Compare Competitors"];

export default function App() {
  const [tab, setTab]           = useState("Overview");
  const [stats, setStats]       = useState(null);
  const [topics, setTopics]     = useState(null);
  const [competitors, setComps] = useState([]);
  const [aiStatus, setAiStatus] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    api("/api/stats").then(setStats).catch(()=>{});
    api("/api/topics").then(setTopics).catch(()=>{});
    api("/api/competitors").then(d=>setComps(d.competitors||[])).catch(()=>{});
  }, []);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setAiStatus("Starting...");
    try {
      await fetch(`${API}/api/analyze`, { method:"POST" });
      setAiStatus("Running (~45s)...");
      const poll = setInterval(async () => {
        const s = await api("/api/analyze/status");
        setAiStatus(s.message||"");
        if (!s.running) { clearInterval(poll); setAnalyzing(false); }
      }, 3000);
    } catch {
      setAiStatus("❌ Failed");
      setAnalyzing(false);
    }
  };

  return (
    <div style={{ minHeight:"100vh", background:"#0b0b14",
      color:"#d2d2f0", fontFamily:"'Inter',system-ui,sans-serif" }}>
      <style>{`
        * { box-sizing:border-box; }
        @keyframes spin { to { transform:rotate(360deg); } }
        ::-webkit-scrollbar { width:6px; height:6px; }
        ::-webkit-scrollbar-track { background:#0b0b14; }
        ::-webkit-scrollbar-thumb { background:#232343; border-radius:4px; }
      `}</style>

      {/* Navbar */}
      <div style={{ background:"#0f0f23", borderBottom:"1px solid #232343",
        padding:"0 32px", display:"flex", alignItems:"center",
        justifyContent:"space-between", height:58,
        position:"sticky", top:0, zIndex:100 }}>
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <img 
  src="/src/assets/logo.png" 
  alt="SEESEC Logo"
  style={{ 
    width: 50, 
    height: 50, 
    borderRadius: 8,
    objectFit: "contain"
  }}
/>
          <span style={{ fontWeight:800, fontSize:25, color:"#fff",
            letterSpacing:"0.02em" }}>SEESEC</span>
          <span style={{ color:"#3d3d6b", fontSize:20 }}>/</span>
          <span style={{ color:"#7e7eb2", fontSize:20 }}>
            Competitor Intelligence
          </span>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          {aiStatus && (
            <span style={{ fontSize:12, fontWeight:500,
              color: aiStatus.includes("❌") ? "#ef4444"
                : aiStatus.includes("✅") ? "#10b981" : "#f59e0b",
              background:"#0f0f23", padding:"5px 12px",
              borderRadius:6, border:"1px solid #232343" }}>
              {aiStatus}
            </span>
          )}
          <button onClick={runAnalysis} disabled={analyzing} style={{
            background: analyzing ? "#1d1d36"
              :"linear-gradient(135deg,#6366f1,#8b5cf6)",
            border:"none", borderRadius:8,
            color: analyzing ? "#6b6b9a":"#fff",
            padding:"8px 18px", fontSize:12, fontWeight:600,
            cursor: analyzing ? "not-allowed":"pointer",
            display:"flex", alignItems:"center", gap:8,
            boxShadow: analyzing ? "none":"0 4px 14px rgba(99,102,241,0.3)"
          }}>
            {analyzing && (
              <div style={{ width:12, height:12,
                border:"2px solid #6b6b9a",
                borderTopColor:"transparent", borderRadius:"50%",
                animation:"spin 0.7s linear infinite" }}/>
            )}
            {analyzing ? "Analyzing..." : "⚡ Run AI Analysis"}
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ background:"#0f0f23", borderBottom:"1px solid #232343",
        padding:"0 32px", display:"flex", gap:2 }}>
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            background:"none", border:"none",
            borderBottom: tab===t ? "3px solid #6366f1":"3px solid transparent",
            color: tab===t ? "#fff":"#6b6b9a",
            padding:"15px 20px", fontSize:13,
            fontWeight: tab===t ? 600:500, cursor:"pointer",
            transition:"color 0.2s"
          }}>{t}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding:"32px", maxWidth:1300, margin:"0 auto" }}>
        {tab==="Overview"           && <OverviewTab stats={stats} topics={topics}/>}
        {tab==="Content Feed"       && <ContentTab competitors={competitors}/>}
        {tab==="Opportunities"      && <OpportunitiesTab/>}
        {tab==="Compare Competitors" && <CompareTab topics={topics} stats={stats}/>}
      </div>
    </div>
  );
}
