import React, { useState, useRef, useEffect } from "react";
import { API_BASE as API } from "./config";

async function apiGet(path) {
  const r = await fetch(API + path);
  return r.json();
}

async function apiPost(path) {
  const r = await fetch(API + path, {
    method: "POST"
  });
  return r.json();
}

function Card({ children, style = {} }) {
  return (
    <div
      style={{
        background: "#16162a",
        border: "1px solid #232343",
        borderRadius: 14,
        padding: "24px",
        boxShadow: "0 4px 24px rgba(0,0,0,0.25)",
        ...style
      }}
    >
      {children}
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div
      style={{
        color: "#a4a4d0",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        marginBottom: 18
      }}
    >
      {children}
    </div>
  );
}

function Badge({ text, color = "#6366f1" }) {
  return (
    <span
      style={{
        background: `${color}15`,
        color,
        border: `1px solid ${color}35`,
        borderRadius: 6,
        padding: "3px 10px",
        fontSize: 11,
        fontWeight: 600
      }}
    >
      {text}
    </span>
  );
}


// ============================================================
// ANALYSIS STAGES
// ============================================================

const STAGES = [
  { key: "starting", label: "Starting analysis" },
  { key: "scraping", label: "Discovering & scraping pages" },
  { key: "scraping_complete", label: "Scraping complete" },
  { key: "saving", label: "Saving to database" },
  { key: "ai_analysis", label: "Generating AI intelligence" },
  { key: "finalizing", label: "Finalizing results" },
  { key: "completed", label: "Complete" }
];


// ============================================================
// PROGRESS CHECKLIST
// ============================================================

function ProgressChecklist({ status }) {
  if (!status) return null;
    const stageIndex = STAGES.findIndex(s => s.key === status.stage);

  if (status.stage === "no_content") {
    return (
      <Card style={{ borderLeft:"4px solid #f59e0b" }}>
        <SectionTitle>Live Progress</SectionTitle>
        <div style={{ display:"flex", alignItems:"flex-start", gap:12 }}>
          <span style={{ fontSize:20 }}>⚠️</span>
          <div>
            <div style={{ color:"#f59e0b", fontWeight:700, fontSize:14, marginBottom:6 }}>
              No content found
            </div>
            <div style={{ color:"#d2d2f0", fontSize:13, lineHeight:1.6 }}>
              {status.message}
            </div>
            {status.pages_discovered > 0 && (
              <div style={{ color:"#6b6b9a", fontSize:12, marginTop:10 }}>
                {status.pages_discovered} pages discovered, {status.pages_scanned} scanned —
                none matched our article/blog detection.
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <SectionTitle>Live Progress</SectionTitle>

      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            height: 8,
            background: "#0f0f23",
            borderRadius: 4,
            overflow: "hidden"
          }}
        >
          <div
            style={{
              width: `${status.progress || 0}%`,
              height: "100%",
              background:
                status.stage === "failed"
                  ? "#ef4444"
                  : "linear-gradient(90deg,#6366f1,#8b5cf6)",
              borderRadius: 4,
              transition: "width 0.4s ease"
            }}
          />
        </div>

        <div
          style={{
            color: "#7e7eb2",
            fontSize: 12,
            marginTop: 8
          }}
        >
          {status.message}
        </div>
      </div>


      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 10
        }}
      >
        {STAGES.map((s, i) => {
          const done =
            status.stage === "completed" ||
            i < stageIndex ||
            (status.stage === "failed" && i < stageIndex);

          const active = s.key === status.stage;

          const failed =
            status.stage === "failed" && active;

          const color = failed
            ? "#ef4444"
            : done
              ? "#10b981"
              : active
                ? "#6366f1"
                : "#3d3d5c";

          return (
            <div
              key={s.key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10
              }}
            >
              <span
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  border: `2px solid ${color}`,
                  background: done ? color : "transparent",
                  flexShrink: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 10,
                  color: "#fff"
                }}
              >
                {done && !failed ? "✓" : failed ? "✕" : ""}
              </span>

              <span
                style={{
                  color: active
                    ? "#fff"
                    : done
                      ? "#d2d2f0"
                      : "#5a5a88",
                  fontSize: 13,
                  fontWeight: active ? 600 : 400
                }}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>


      {(status.pages_discovered > 0 ||
        status.articles_found > 0) && (
        <div
          style={{
            display: "flex",
            gap: 24,
            marginTop: 20,
            paddingTop: 16,
            borderTop: "1px solid #232343"
          }}
        >
          <div>
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 10,
                textTransform: "uppercase"
              }}
            >
              Pages Discovered
            </div>

            <div
              style={{
                color: "#6366f1",
                fontSize: 20,
                fontWeight: 700
              }}
            >
              {status.pages_discovered}
            </div>
          </div>


          <div>
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 10,
                textTransform: "uppercase"
              }}
            >
              Pages Scanned
            </div>

            <div
              style={{
                color: "#06b6d4",
                fontSize: 20,
                fontWeight: 700
              }}
            >
              {status.pages_scanned}
            </div>
          </div>


          <div>
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 10,
                textTransform: "uppercase"
              }}
            >
              Articles Found
            </div>

            <div
              style={{
                color: "#10b981",
                fontSize: 20,
                fontWeight: 700
              }}
            >
              {status.articles_found}
            </div>
          </div>
        </div>
      )}


      {status.error && (
        <div
          style={{
            marginTop: 16,
            padding: "12px 16px",
            background: "#ef444415",
            border: "1px solid #ef444435",
            borderRadius: 8,
            color: "#ef4444",
            fontSize: 12
          }}
        >
          {status.error}
        </div>
      )}
    </Card>
  );
}


// ============================================================
// EXPORT TO PDF
// ============================================================

function exportToPDF(result, parsedSummary) {
  const w = window.open("", "_blank");

  if (!w) return;

  const esc = (s) =>
    (s || "")
      .toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");


  const gapRows = (
    parsedSummary?.content_gap_analysis || []
  )
    .map(
      (g) => `
        <div
          style="
            border-left:4px solid #6366f1;
            padding:10px 16px;
            margin-bottom:12px;
            background:#f5f5fa;
          "
        >
          <div style="font-weight:700;">
            ${esc(g.topic)}
            —
            ${esc(g.priority)} priority
            (${g.competitor_article_count} competitor articles)
          </div>

          <div style="margin:6px 0; color:#333;">
            ${esc(g.assessment)}
          </div>

          <div style="color:#065f46; font-weight:600;">
            → ${esc(g.seesec_action)}
          </div>
        </div>
      `
    )
    .join("");


  const articleRows = (result.articles || [])
    .slice(0, 30)
    .map(
      (a) => `
        <tr>
          <td
            style="
              padding:6px 10px;
              border-bottom:1px solid #ddd;
            "
          >
            ${esc(a.title)}
          </td>

          <td
            style="
              padding:6px 10px;
              border-bottom:1px solid #ddd;
            "
          >
            ${esc(a.content_type)}
          </td>

          <td
            style="
              padding:6px 10px;
              border-bottom:1px solid #ddd;
            "
          >
            ${esc(a.published_date) || "—"}
          </td>
        </tr>
      `
    )
    .join("");


  const html = `
  <html>

  <head>

    <title>
      SEESEC Report — ${esc(result.company)}
    </title>

    <style>

      body {
        font-family: Arial, sans-serif;
        color: #111;
        padding: 40px;
        max-width: 800px;
        margin: 0 auto;
      }

      h1 {
        color: #4338ca;
        margin-bottom: 4px;
      }

      h2 {
        color: #4338ca;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 6px;
        margin-top: 32px;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }

      th {
        text-align: left;
        padding: 6px 10px;
        background: #f5f5fa;
      }

      .meta {
        color: #555;
        font-size: 13px;
        margin-bottom: 20px;
      }

      .badge {
        display: inline-block;
        background: #ede9fe;
        color: #5b21b6;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 12px;
        margin: 2px;
      }

      .warning {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        color: #92400e;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 13px;
      }

    </style>

  </head>


  <body>

    <h1>SEESEC Competitor Intelligence Report</h1>

    <div class="meta">

      <b>${esc(result.company)}</b>

      &nbsp;|&nbsp;

      ${esc(result.website)}

      &nbsp;|&nbsp;

      Generated: ${new Date().toLocaleString()}

      &nbsp;|&nbsp;

      Last scraped: ${esc(result.last_scraped)}

    </div>


    ${
      !parsedSummary && !result.ai_summary
        ? `
          <div class="warning">

            ⚠️ No AI analysis found for this company yet.

            This report only contains scraped articles below.

            Go back and click "Refresh Analysis" to generate the
            AI strategy, gap analysis, and recommendations,
            then export again.

          </div>
        `
        : ""
    }


    <h2>Content Strategy</h2>

    <p>
      ${
        esc(parsedSummary?.marketing_strategy) ||
        esc(result.ai_summary) ||
        "Not yet generated."
      }
    </p>


    <h2>Top Topics</h2>

    <div>
      ${
        (parsedSummary?.top_topics || [])
          .map(
            (t) =>
              `<span class="badge">${esc(t)}</span>`
          )
          .join("") ||
        "<p>Not yet generated.</p>"
      }
    </div>


    <h2>Products & Services</h2>

    <ul>
      ${
        (parsedSummary?.products_services || [])
          .map(
            (p) => `<li>${esc(p)}</li>`
          )
          .join("") ||
        "<p>Not yet generated.</p>"
      }
    </ul>


    <h2>Content Gap Analysis vs SEESEC</h2>

    ${
      gapRows ||
      "<p>Not yet generated.</p>"
    }


    <h2>Recommendations for SEESEC</h2>

    <ul>
      ${
        (parsedSummary?.seesec_recommendations || [])
          .map(
            (r) => `<li>${esc(r)}</li>`
          )
          .join("") ||
        "<p>Not yet generated.</p>"
      }
    </ul>


    <h2>
      Recent Articles
      (${result.articles?.length || 0} total,
      showing up to 30)
    </h2>


    <table>

      <thead>

        <tr>
          <th>Title</th>
          <th>Type</th>
          <th>Date</th>
        </tr>

      </thead>


      <tbody>
        ${articleRows}
      </tbody>

    </table>

  </body>

  </html>
  `;


  w.document.write(html);
  w.document.close();
  w.focus();

  setTimeout(() => {
    w.print();
  }, 400);
}


// ============================================================
// RESULTS VIEW
// ============================================================

function ResultsView({ result }) {
  if (!result || result.error) {
    return (
      <Card>
        <div
          style={{
            color: "#ef4444",
            fontSize: 13
          }}
        >
          {result?.error || "No results available."}
        </div>
      </Card>
    );
  }


  let parsedSummary = null;

  try {
    let cleaned = (result.ai_summary || "").trim();

    cleaned = cleaned
      .replace(/^```json\s*/i, "")
      .replace(/^```\s*/i, "")
      .replace(/```\s*$/, "");

    parsedSummary = JSON.parse(cleaned);

  } catch {
    // AI summary is not valid JSON.
  }


  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 24
      }}
    >


      {/* COMPETITOR PROFILE */}

      <Card
        style={{
          borderLeft: "4px solid #6366f1",
          background:
            "linear-gradient(135deg,#1a1a35,#16162a)"
        }}
      >

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start"
          }}
        >

          <SectionTitle>
            Competitor Profile — {result.company}
          </SectionTitle>


          <button
            onClick={() =>
              exportToPDF(result, parsedSummary)
            }
            style={{
              background: "#0f0f23",
              border: "1px solid #232343",
              borderRadius: 8,
              color: "#d2d2f0",
              padding: "6px 14px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              flexShrink: 0
            }}
          >
            📄 Export PDF
          </button>

        </div>


        {/* NEW WARNING FOR MISSING AI DATA */}

        {!parsedSummary && !result.ai_summary && (
          <div
            style={{
              background: "#f59e0b15",
              border: "1px solid #f59e0b35",
              borderRadius: 8,
              padding: "10px 16px",
              color: "#f59e0b",
              fontSize: 12.5,
              marginBottom: 16
            }}
          >
            ⚠️ No AI analysis found yet for this company.
            Click "Refresh Analysis" above to generate it.
          </div>
        )}


        <div
          style={{
            display: "flex",
            gap: 24,
            marginBottom: 16,
            flexWrap: "wrap"
          }}
        >

          <div>
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 10,
                textTransform: "uppercase"
              }}
            >
              Website
            </div>

            <a
              href={result.website}
              target="_blank"
              rel="noreferrer"
              style={{
                color: "#06b6d4",
                fontSize: 13
              }}
            >
              {result.website}
            </a>
          </div>


          <div>
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 10,
                textTransform: "uppercase"
              }}
            >
              Articles
            </div>

            <div
              style={{
                color: "#10b981",
                fontSize: 16,
                fontWeight: 700
              }}
            >
              {result.article_count}
            </div>
          </div>


          <div>
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 10,
                textTransform: "uppercase"
              }}
            >
              Last Scraped
            </div>

            <div
              style={{
                color: "#d2d2f0",
                fontSize: 13
              }}
            >
              {result.last_scraped || "—"}
            </div>
          </div>

        </div>


        {/* SOCIAL LINKS */}

        {(() => {
          let social = {};

          try {
            social = JSON.parse(
              result.social_links || "{}"
            );
          } catch {}

          const entries = Object.entries(social)
            .filter(([, v]) => v);

          if (!entries.length) return null;

          return (
            <div style={{ marginBottom: 16 }}>

              <div
                style={{
                  color: "#a4a4d0",
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  marginBottom: 8
                }}
              >
                Social Presence
              </div>


              <div
                style={{
                  display: "flex",
                  gap: 10,
                  flexWrap: "wrap"
                }}
              >
                {entries.map(
                  ([platform, url]) => (
                    <a
                      key={platform}
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        background: "#0f0f23",
                        border: "1px solid #232343",
                        borderRadius: 8,
                        padding: "6px 14px",
                        color: "#06b6d4",
                        fontSize: 12,
                        textDecoration: "none",
                        textTransform: "capitalize"
                      }}
                    >
                      {platform}
                    </a>
                  )
                )}
              </div>

            </div>
          );
        })()}


        {/* TECHNOLOGY STACK */}

        {(() => {
          let tech = [];

          try {
            tech = JSON.parse(
              result.tech_stack || "[]"
            );
          } catch {}

          if (!tech.length) return null;

          return (
            <div style={{ marginBottom: 16 }}>

              <div
                style={{
                  color: "#a4a4d0",
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  marginBottom: 8
                }}
              >
                Technology Stack
              </div>


              <div
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap"
                }}
              >
                {tech.map((t, i) => (
                  <span
                    key={i}
                    title={t.category}
                    style={{
                      background: "#0f0f23",
                      border: "1px solid #232343",
                      borderRadius: 8,
                      padding: "6px 14px",
                      color: "#a78bfa",
                      fontSize: 12
                    }}
                  >
                    {t.name}

                    <span
                      style={{
                        color: "#6b6b9a",
                        fontSize: 10,
                        marginLeft: 6
                      }}
                    >
                      {t.category}
                    </span>

                  </span>
                ))}
              </div>

            </div>
          );
        })()}


        {/* AI SUMMARY */}

        {parsedSummary ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 14
            }}
          >

            {parsedSummary.marketing_strategy && (
              <div>

                <div
                  style={{
                    color: "#a4a4d0",
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    marginBottom: 6
                  }}
                >
                  Content Strategy
                </div>

                <p
                  style={{
                    color: "#d2d2f0",
                    fontSize: 13,
                    lineHeight: 1.7,
                    margin: 0
                  }}
                >
                  {parsedSummary.marketing_strategy}
                </p>

              </div>
            )}


            {parsedSummary.top_topics?.length > 0 && (
              <div>

                <div
                  style={{
                    color: "#a4a4d0",
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    marginBottom: 6
                  }}
                >
                  Top Topics
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    flexWrap: "wrap"
                  }}
                >
                  {parsedSummary.top_topics.map(
                    (t, i) => (
                      <Badge
                        key={i}
                        text={t}
                        color="#8b5cf6"
                      />
                    )
                  )}
                </div>

              </div>
            )}


            {parsedSummary.products_services?.length > 0 && (
              <div>

                <div
                  style={{
                    color: "#a4a4d0",
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    marginBottom: 6
                  }}
                >
                  Products & Services
                </div>

                <ul
                  style={{
                    margin: 0,
                    paddingLeft: 18,
                    color: "#cbd5e1",
                    fontSize: 13,
                    lineHeight: 1.8
                  }}
                >
                  {parsedSummary.products_services.map(
                    (p, i) => (
                      <li key={i}>{p}</li>
                    )
                  )}
                </ul>

              </div>
            )}


            {parsedSummary.leadership?.length > 0 && (
              <div>

                <div
                  style={{
                    color: "#a4a4d0",
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    marginBottom: 6
                  }}
                >
                  Leadership
                </div>

                <ul
                  style={{
                    margin: 0,
                    paddingLeft: 18,
                    color: "#cbd5e1",
                    fontSize: 13,
                    lineHeight: 1.8
                  }}
                >
                  {parsedSummary.leadership.map(
                    (p, i) => (
                      <li key={i}>{p}</li>
                    )
                  )}
                </ul>

              </div>
            )}


            {parsedSummary.seesec_recommendations?.length > 0 && (
              <div>

                <div
                  style={{
                    color: "#a4a4d0",
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    marginBottom: 6
                  }}
                >
                  Recommendations
                </div>

                <ul
                  style={{
                    margin: 0,
                    paddingLeft: 18,
                    color: "#cbd5e1",
                    fontSize: 13,
                    lineHeight: 1.8
                  }}
                >
                  {parsedSummary.seesec_recommendations.map(
                    (r, i) => (
                      <li key={i}>{r}</li>
                    )
                  )}
                </ul>

              </div>
            )}

          </div>

        ) : (

          <p
            style={{
              color: "#d2d2f0",
              fontSize: 13,
              lineHeight: 1.7
            }}
          >
            {result.ai_summary || "AI analysis has not been generated yet."}
          </p>

        )}

      </Card>


      {/* CONTENT INTELLIGENCE */}

      <Card>

        <SectionTitle>
          Content Intelligence Stats
        </SectionTitle>


        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 24
          }}
        >

          <div>

            <div
              style={{
                color: "#a4a4d0",
                fontSize: 11,
                fontWeight: 700,
                textTransform: "uppercase",
                marginBottom: 10
              }}
            >
              Content Type Breakdown
            </div>


            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 8
              }}
            >
              {(result.content_type_breakdown || []).length
                ? result.content_type_breakdown.map(
                    (t) => (
                      <div
                        key={t.type}
                        style={{
                          display: "flex",
                          justifyContent: "space-between"
                        }}
                      >
                        <span
                          style={{
                            color: "#d2d2f0",
                            fontSize: 12
                          }}
                        >
                          {t.type}
                        </span>

                        <Badge
                          text={t.count}
                          color="#06b6d4"
                        />

                      </div>
                    )
                  )
                : (
                  <div
                    style={{
                      color: "#6b6b9a",
                      fontSize: 12
                    }}
                  >
                    No data.
                  </div>
                )}
            </div>


            <div
              style={{
                color: "#a4a4d0",
                fontSize: 11,
                fontWeight: 700,
                textTransform: "uppercase",
                marginTop: 20,
                marginBottom: 10
              }}
            >
              Publishing Frequency
            </div>


            <div
              style={{
                color: "#d2d2f0",
                fontSize: 13,
                lineHeight: 1.6
              }}
            >
              {result.publishing_frequency?.summary ||
                "Not enough data."}
            </div>

          </div>


          <div>

            <div
              style={{
                color: "#a4a4d0",
                fontSize: 11,
                fontWeight: 700,
                textTransform: "uppercase",
                marginBottom: 10
              }}
            >
              Trending Keywords
            </div>


            <div
              style={{
                display: "flex",
                gap: 8,
                flexWrap: "wrap"
              }}
            >
              {(result.trending_keywords || []).length
                ? result.trending_keywords.map(
                    (k) => (
                      <Badge
                        key={k.word}
                        text={`${k.word} (${k.count})`}
                        color="#f59e0b"
                      />
                    )
                  )
                : (
                  <div
                    style={{
                      color: "#6b6b9a",
                      fontSize: 12
                    }}
                  >
                    No data.
                  </div>
                )}
            </div>

          </div>

        </div>

      </Card>


      {/* CONTENT GAP ANALYSIS */}

      {parsedSummary?.content_gap_analysis?.length > 0 && (
        <Card>

          <SectionTitle>
            Content Gap Analysis vs SEESEC
          </SectionTitle>


          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 14
            }}
          >

            {parsedSummary.content_gap_analysis.map(
              (g, i) => {
                const priorityColor =
                  g.priority === "High"
                    ? "#ef4444"
                    : g.priority === "Medium"
                      ? "#f59e0b"
                      : "#10b981";

                return (
                  <div
                    key={i}
                    style={{
                      background: "#0f0f23",
                      border: "1px solid #232343",
                      borderLeft: `4px solid ${priorityColor}`,
                      borderRadius: 10,
                      padding: "16px 20px"
                    }}
                  >

                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 8,
                        flexWrap: "wrap",
                        gap: 8
                      }}
                    >

                      <div
                        style={{
                          color: "#e2e2f8",
                          fontWeight: 700,
                          fontSize: 14
                        }}
                      >
                        {g.topic}
                      </div>


                      <div
                        style={{
                          display: "flex",
                          gap: 8,
                          alignItems: "center"
                        }}
                      >

                        <span
                          style={{
                            color: "#6b6b9a",
                            fontSize: 11
                          }}
                        >
                          {g.competitor_article_count}
                          {" "}competitor articles
                        </span>

                        <Badge
                          text={g.priority}
                          color={priorityColor}
                        />

                      </div>

                    </div>


                    <p
                      style={{
                        color: "#cbd5e1",
                        fontSize: 13,
                        lineHeight: 1.7,
                        margin: "0 0 10px 0"
                      }}
                    >
                      {g.assessment}
                    </p>


                    <div
                      style={{
                        color: "#10b981",
                        fontSize: 13,
                        fontWeight: 500
                      }}
                    >
                      → {g.seesec_action}
                    </div>

                  </div>
                );
              }
            )}

          </div>

        </Card>
      )}


      {/* ARTICLES */}

      <Card>

        <SectionTitle>
          Articles ({result.articles?.length || 0})
        </SectionTitle>


        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 2
          }}
        >

          {(result.articles || []).map(
            (a, i) => (
              <div
                key={a.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "10px 4px",
                  borderBottom:
                    i < result.articles.length - 1
                      ? "1px solid #1e1e38"
                      : "none",
                  gap: 12
                }}
              >

                <a
                  href={a.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    color: "#d2d2f0",
                    fontSize: 13,
                    textDecoration: "none",
                    flex: 1
                  }}
                >
                  {a.title}
                </a>


                <Badge
                  text={a.content_type}
                  color="#06b6d4"
                />


                <span
                  style={{
                    color: "#6b6b9a",
                    fontSize: 12,
                    width: 100,
                    textAlign: "right"
                  }}
                >
                  {a.published_date || "—"}
                </span>

              </div>
            )
          )}


          {!result.articles?.length && (
            <div
              style={{
                color: "#6b6b9a",
                fontSize: 13,
                padding: 20,
                textAlign: "center"
              }}
            >
              No articles found.
            </div>
          )}

        </div>

      </Card>

    </div>
  );
}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function SearchAnalyzeTab() {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const pollRef = useRef(null);


  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);


  const runSearch = async () => {
    if (!query.trim()) return;

    setSearching(true);
    setError("");
    setCandidates([]);
    setSelected(null);
    setStatus(null);
    setResult(null);

    try {
      const d = await apiGet(
        `/api/search-company?q=${encodeURIComponent(
          query.trim()
        )}`
      );

      if (d.type === "error") {
        setError(d.message);
      } else {
        setCandidates(d.candidates || []);

        if (!d.candidates?.length) {
          setError("No matching website found.");
        }
      }

    } catch (e) {
      setError(
        "Search failed. Is the backend running?"
      );
    } finally {
      setSearching(false);
    }
  };


  const startAnalysis = async (
    website,
    forceRefresh = false
  ) => {
    const companyName = query.trim();

    setSelected({
      name: companyName,
      website
    });

    setResult(null);
    setError("");

    setStatus({
      running: true,
      stage: "starting",
      message: "Starting analysis...",
      progress: 0
    });


    try {
      const res = await apiPost(
        `/api/analyze-company?company_name=${encodeURIComponent(
          companyName
        )}&website=${encodeURIComponent(
          website
        )}&force_refresh=${forceRefresh}`
      );


      if (res.status === "error") {
        setError(res.message);
        setStatus(null);
        return;
      }


      if (res.status === "cached") {
        setStatus({
          running: false,
          stage: "cached",
          message: res.message,
          progress: 100,
          cachedWebsite: website
        });

        const r = await apiGet(
          `/api/company/${encodeURIComponent(
            companyName
          )}`
        );

        setResult(r);

        return;
      }


      pollRef.current = setInterval(
        async () => {
          const s = await apiGet(
            `/api/analyze-company/status/${encodeURIComponent(
              companyName
            )}`
          );

          setStatus(s);


          if (!s.running && (s.stage === "completed" || s.stage === "failed" || s.stage === "no_content")) {
            clearInterval(pollRef.current);


            if (s.stage === "completed") {
              const r = await apiGet(
                `/api/company/${encodeURIComponent(
                  companyName
                )}`
              );

              setResult(r);
            }
          }
        },
        1500
      );


    } catch (e) {
      setError(
        "Failed to start analysis. Is the backend running?"
      );

      setStatus(null);
    }
  };


  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 24
      }}
    >

      {/* SEARCH BOX */}

      <Card>

        <SectionTitle>
          Search a Competitor
        </SectionTitle>


        <div
          style={{
            display: "flex",
            gap: 12
          }}
        >

          <input
            value={query}
            onChange={(e) =>
              setQuery(e.target.value)
            }
            onKeyDown={(e) =>
              e.key === "Enter" && runSearch()
            }
            placeholder="Enter a company name or website, e.g. Signzy"
            style={{
              flex: 1,
              background: "#0f0f23",
              border: "1px solid #232343",
              borderRadius: 10,
              color: "#d2d2f0",
              padding: "12px 16px",
              fontSize: 14,
              outline: "none"
            }}
            onFocus={(e) =>
              (e.target.style.borderColor =
                "#6366f1")
            }
            onBlur={(e) =>
              (e.target.style.borderColor =
                "#232343")
            }
          />


          <button
            onClick={runSearch}
            disabled={searching}
            style={{
              background: searching
                ? "#1d1d36"
                : "linear-gradient(135deg,#6366f1,#8b5cf6)",
              border: "none",
              borderRadius: 10,
              color: "#fff",
              padding: "12px 24px",
              fontSize: 14,
              fontWeight: 600,
              cursor: searching
                ? "not-allowed"
                : "pointer"
            }}
          >
            {searching
              ? "Searching..."
              : "Search"}
          </button>

        </div>


        {error && (
          <div
            style={{
              marginTop: 14,
              color: "#ef4444",
              fontSize: 13
            }}
          >
            {error}
          </div>
        )}


        {candidates.length > 0 &&
          !selected && (
            <div
              style={{
                marginTop: 18,
                display: "flex",
                flexDirection: "column",
                gap: 8
              }}
            >

              <div
                style={{
                  color: "#6b6b9a",
                  fontSize: 12
                }}
              >
                Select the correct website:
              </div>


              {candidates.map(
                (c, i) => (
                  <button
                    key={i}
                    onClick={() =>
                      startAnalysis(c)
                    }
                    style={{
                      textAlign: "left",
                      background: "#0f0f23",
                      border: "1px solid #232343",
                      borderRadius: 10,
                      color: "#d2d2f0",
                      padding: "12px 16px",
                      fontSize: 13,
                      cursor: "pointer"
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.borderColor =
                        "#6366f1")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.borderColor =
                        "#232343")
                    }
                  >
                    {c}
                  </button>
                )
              )}

            </div>
          )}

      </Card>


      {/* LIVE PROGRESS */}

      {selected &&
        status &&
        status.stage !== "cached" && (
          <ProgressChecklist status={status} />
        )}


      {/* CACHED RESULT */}

      {selected &&
        status &&
        status.stage === "cached" && (

          <Card
            style={{
              borderLeft: "4px solid #f59e0b"
            }}
          >

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 12
              }}
            >

              <div>

                <div
                  style={{
                    color: "#f59e0b",
                    fontWeight: 700,
                    fontSize: 13,
                    marginBottom: 4
                  }}
                >
                  Showing cached data
                </div>


                <div
                  style={{
                    color: "#8a8ab6",
                    fontSize: 12
                  }}
                >
                  {status.message}
                </div>

              </div>


              <button
                onClick={() =>
                  startAnalysis(
                    status.cachedWebsite,
                    true
                  )
                }
                style={{
                  background:
                    "linear-gradient(135deg,#6366f1,#8b5cf6)",
                  border: "none",
                  borderRadius: 10,
                  color: "#fff",
                  padding: "10px 20px",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                  whiteSpace: "nowrap"
                }}
              >
                🔄 Refresh Analysis (re-scrape live)
              </button>

            </div>

          </Card>
        )}


      {/* RESULTS */}

      {result && (
        <ResultsView result={result} />
      )}

    </div>
  );
}