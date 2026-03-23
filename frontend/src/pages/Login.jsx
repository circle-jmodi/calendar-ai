import React from "react";

const API = import.meta.env.VITE_API_URL || "";

export default function Login() {
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>📅</div>
        <h1 style={styles.title}>Calendar AI</h1>
        <p style={styles.subtitle}>
          Your intelligent calendar assistant — replaces Clockwise with AI-powered
          focus time, smart scheduling, and Slack status sync.
        </p>

        <a href={`${API}/auth/google/login`} style={styles.googleBtn}>
          <svg width="18" height="18" viewBox="0 0 18 18" style={{ marginRight: 10 }}>
            <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
            <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
            <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/>
            <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
          </svg>
          Sign in with Google
        </a>

        <div style={styles.features}>
          <Feature icon="🎯" text="AI-powered focus time blocks" />
          <Feature icon="📊" text="Meeting optimization with Claude" />
          <Feature icon="🔗" text="Smart scheduling links" />
          <Feature icon="💬" text="Slack status auto-sync" />
          <Feature icon="🎙️" text="Gong auto-record for Teams meetings" />
        </div>
      </div>
    </div>
  );
}

function Feature({ icon, text }) {
  return (
    <div style={styles.feature}>
      <span style={styles.featureIcon}>{icon}</span>
      <span style={styles.featureText}>{text}</span>
    </div>
  );
}

const styles = {
  container: { display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%)" },
  card: { background: "#fff", borderRadius: 16, padding: "48px 40px", maxWidth: 440, width: "100%", boxShadow: "0 4px 24px rgba(0,0,0,0.08)", textAlign: "center" },
  logo: { fontSize: 48, marginBottom: 12 },
  title: { fontSize: 28, fontWeight: 700, color: "#1e293b", marginBottom: 8 },
  subtitle: { color: "#64748b", lineHeight: 1.6, marginBottom: 32, fontSize: 15 },
  googleBtn: {
    display: "inline-flex", alignItems: "center", padding: "12px 24px", border: "1px solid #e2e8f0",
    borderRadius: 8, background: "#fff", color: "#1e293b", textDecoration: "none",
    fontWeight: 500, fontSize: 15, cursor: "pointer", transition: "box-shadow 0.2s",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  features: { marginTop: 32, textAlign: "left", display: "flex", flexDirection: "column", gap: 12 },
  feature: { display: "flex", alignItems: "center", gap: 12 },
  featureIcon: { fontSize: 18, width: 24, textAlign: "center" },
  featureText: { color: "#475569", fontSize: 14 },
};
