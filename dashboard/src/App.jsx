import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell
} from "recharts";
import SearchAnalyzeTab from "./SearchAnalyzeTab";
import Login from "./Login";
import CompareCompaniesTab from "./CompareCompaniesTab";
import { API_BASE as API } from "./config";

const COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#06b6d4",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#ec4899"
];

const COMP_COLORS = {
  AuthBridge:"#6366f1",
  IDfy:"#8b5cf6",
  Signzy:"#06b6d4",
  HyperVerge:"#10b981",
  Bureau:"#f59e0b",
  DigiTap:"#ef4444"
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

const TABS = ["Analyze Competitor","Overview","Content Feed","Compare Competitors","Side-by-Side"];

export default function App() {
  const [authed, setAuthed]     = useState(
    localStorage.getItem("seesec_authed") === "true"
  );
  const [tab, setTab]           = useState("Overview");
  const [stats, setStats]       = useState(null);
  const [topics, setTopics]     = useState(null);
  const [competitors, setComps] = useState([]);

  useEffect(() => {
    api("/api/stats").then(setStats).catch(()=>{});
    api("/api/topics").then(setTopics).catch(()=>{});
    api("/api/competitors").then(d=>setComps(d.competitors||[])).catch(()=>{});
  }, []);

  if (!authed) {
    return <Login onSuccess={() => setAuthed(true)} />;
  }

  return (
    <div style={{ minHeight:"120vh", background:"#0b0b14",
      color:"#d2d2f0", fontFamily:"'Poppins',system-ui,sans-serif" }}>
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
        <div style={{ display: tab==="Analyze Competitor" ? "block" : "none" }}>
          <SearchAnalyzeTab/>
        </div>
        {tab==="Overview"           && <OverviewTab stats={stats} topics={topics}/>}
        {tab==="Content Feed"       && <ContentTab competitors={competitors}/>}
        {tab==="Compare Competitors" && <CompareTab topics={topics} stats={stats}/>}
        {tab==="Side-by-Side"        && <CompareCompaniesTab/>}
      </div>
    </div>
  );
}