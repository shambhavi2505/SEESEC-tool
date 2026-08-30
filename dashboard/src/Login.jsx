import React, { useState } from "react";

// Simple demo password gate.
// Not real auth/security — just enough to satisfy "log into the tool"
// for a demo. Change this password before showing it to anyone external.
const DEMO_PASSWORD = "Seesec@2026";

export default function Login({ onSuccess }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === DEMO_PASSWORD) {
      localStorage.setItem("seesec_authed", "true");
      onSuccess();
    } else {
      setError("Incorrect password.");
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "#0a0a18"
    }}>
      <form onSubmit={handleSubmit} style={{
        background: "#16162a", border: "1px solid #232343", borderRadius: 16,
        padding: "40px", width: 340, boxShadow: "0 8px 32px rgba(0,0,0,0.4)"
      }}>
        <div style={{ color: "#fff", fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
          SEESEC
        </div>
        <div style={{ color: "#8a8ab6", fontSize: 13, marginBottom: 24 }}>
          Competitor Intelligence Platform
        </div>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter password"
          autoFocus
          style={{
            width: "100%", boxSizing: "border-box", background: "#0f0f23",
            border: "1px solid #232343", borderRadius: 10, color: "#d2d2f0",
            padding: "12px 16px", fontSize: 14, outline: "none", marginBottom: 12
          }}
        />

        {error && (
          <div style={{ color: "#ef4444", fontSize: 13, marginBottom: 12 }}>{error}</div>
        )}

        <button type="submit" style={{
          width: "100%", background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
          border: "none", borderRadius: 10, color: "#fff", padding: "12px 0",
          fontSize: 14, fontWeight: 600, cursor: "pointer"
        }}>
          Log In
        </button>
      </form>
    </div>
  );
}