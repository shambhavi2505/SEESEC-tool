// Central place for the backend API base URL.
//
// Locally (npm run dev), this falls back to localhost:8000.
// In production (deployed on Vercel), set VITE_API_URL as an
// environment variable pointing to your deployed backend, e.g.
// https://seesec-backend.onrender.com
//
// Vite only exposes env vars prefixed with VITE_ to the browser.

export const API_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";