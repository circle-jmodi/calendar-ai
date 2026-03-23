import React, { useState } from "react";

const API = import.meta.env.VITE_API_URL || "";

const STEPS = [
  { id: "welcome", label: "Welcome" },
  { id: "google", label: "Google OAuth" },
  { id: "slack", label: "Slack (optional)" },
  { id: "anthropic", label: "Anthropic" },
  { id: "done", label: "Done" },
];

function StepSidebar({ currentStep }) {
  return (
    <aside style={s.sidebar}>
      <div style={s.sidebarTitle}>Setup</div>
      {STEPS.map((step, i) => {
        const currentIdx = STEPS.findIndex((st) => st.id === currentStep);
        const done = i < currentIdx;
        const active = step.id === currentStep;
        return (
          <div key={step.id} style={{ ...s.stepItem, ...(active ? s.stepActive : {}), ...(done ? s.stepDone : {}) }}>
            <span style={s.stepDot}>{done ? "✓" : i + 1}</span>
            <span>{step.label}</span>
          </div>
        );
      })}
    </aside>
  );
}

function FieldGroup({ label, id, type = "text", value, onChange, placeholder, hint }) {
  return (
    <div style={s.fieldGroup}>
      <label htmlFor={id} style={s.label}>{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={s.input}
        autoComplete="off"
      />
      {hint && <p style={s.hint}>{hint}</p>}
    </div>
  );
}

export default function SetupWizard({ onComplete }) {
  const [step, setStep] = useState("welcome");
  const [form, setForm] = useState({
    google_client_id: "",
    google_client_secret: "",
    slack_client_id: "",
    slack_client_secret: "",
    slack_signing_secret: "",
    slack_bot_token: "",
    anthropic_api_key: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (field) => (val) => setForm((f) => ({ ...f, [field]: val }));

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API}/setup/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }
      setStep("done");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={s.shell}>
      <StepSidebar currentStep={step} />
      <main style={s.content}>
        {step === "welcome" && (
          <div>
            <h1 style={s.h1}>Welcome to Calendar AI</h1>
            <p style={s.body}>
              This wizard will help you configure the app for first use. You'll need:
            </p>
            <ul style={s.list}>
              <li>A <strong>Google OAuth 2.0</strong> client (for Calendar access)</li>
              <li>An <strong>Anthropic API key</strong> (for AI optimization)</li>
              <li>A <strong>Slack app</strong> (optional — for status sync and slash commands)</li>
            </ul>
            <p style={s.body}>
              Credentials are saved to the <code style={s.code}>.env</code> file on the server.
              Once saved, this wizard won't appear again.
            </p>
            <button style={s.btn} onClick={() => setStep("google")}>Get Started →</button>
          </div>
        )}

        {step === "google" && (
          <div>
            <h1 style={s.h1}>Google OAuth</h1>
            <p style={s.body}>
              Create an OAuth 2.0 client in the{" "}
              <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer" style={s.link}>
                Google Cloud Console
              </a>
              . Set the redirect URI to{" "}
              <code style={s.code}>http://localhost:8000/auth/google/callback</code>{" "}
              (or your production URL).
            </p>
            <FieldGroup
              label="Client ID"
              id="google_client_id"
              value={form.google_client_id}
              onChange={set("google_client_id")}
              placeholder="12345-abc.apps.googleusercontent.com"
            />
            <FieldGroup
              label="Client Secret"
              id="google_client_secret"
              type="password"
              value={form.google_client_secret}
              onChange={set("google_client_secret")}
              placeholder="GOCSPX-..."
            />
            <div style={s.row}>
              <button style={s.btnSecondary} onClick={() => setStep("welcome")}>← Back</button>
              <button
                style={s.btn}
                disabled={!form.google_client_id || !form.google_client_secret}
                onClick={() => setStep("slack")}
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {step === "slack" && (
          <div>
            <h1 style={s.h1}>Slack <span style={s.badge}>Optional</span></h1>
            <p style={s.body}>
              Connect a Slack app to enable status sync and slash commands (
              <code style={s.code}>/focus-time</code>, <code style={s.code}>/optimize</code>, etc.).
              Skip this step if you don't need Slack integration.
            </p>
            <FieldGroup
              label="Client ID"
              id="slack_client_id"
              value={form.slack_client_id}
              onChange={set("slack_client_id")}
              placeholder="12345.67890"
            />
            <FieldGroup
              label="Client Secret"
              id="slack_client_secret"
              type="password"
              value={form.slack_client_secret}
              onChange={set("slack_client_secret")}
              placeholder="abc123..."
            />
            <FieldGroup
              label="Signing Secret"
              id="slack_signing_secret"
              type="password"
              value={form.slack_signing_secret}
              onChange={set("slack_signing_secret")}
              placeholder="abc123..."
              hint="Used to verify slash command requests from Slack."
            />
            <FieldGroup
              label="Bot Token"
              id="slack_bot_token"
              type="password"
              value={form.slack_bot_token}
              onChange={set("slack_bot_token")}
              placeholder="xoxb-..."
              hint="Found in OAuth & Permissions in your Slack app settings."
            />
            <div style={s.row}>
              <button style={s.btnSecondary} onClick={() => setStep("google")}>← Back</button>
              <button style={s.btnSecondary} onClick={() => setStep("anthropic")}>Skip</button>
              <button style={s.btn} onClick={() => setStep("anthropic")}>Next →</button>
            </div>
          </div>
        )}

        {step === "anthropic" && (
          <div>
            <h1 style={s.h1}>Anthropic API Key</h1>
            <p style={s.body}>
              The app uses Claude to analyze your calendar and create optimized focus blocks.
              Get your API key from{" "}
              <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" style={s.link}>
                console.anthropic.com
              </a>
              .
            </p>
            <FieldGroup
              label="API Key"
              id="anthropic_api_key"
              type="password"
              value={form.anthropic_api_key}
              onChange={set("anthropic_api_key")}
              placeholder="sk-ant-..."
            />
            {error && <p style={s.error}>{error}</p>}
            <div style={s.row}>
              <button style={s.btnSecondary} onClick={() => setStep("slack")}>← Back</button>
              <button
                style={s.btn}
                disabled={!form.anthropic_api_key || saving}
                onClick={handleSave}
              >
                {saving ? "Saving…" : "Save & Finish"}
              </button>
            </div>
          </div>
        )}

        {step === "done" && (
          <div style={s.doneWrap}>
            <div style={s.checkCircle}>✓</div>
            <h1 style={s.h1}>You're all set!</h1>
            <p style={s.body}>
              Credentials have been saved. The app is ready to use.
            </p>
            <button style={s.btn} onClick={onComplete}>
              Sign in with Google →
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

const s = {
  shell: { display: "flex", minHeight: "100vh", background: "#f8fafc", fontFamily: "system-ui, sans-serif" },
  sidebar: { width: 220, background: "#1e293b", padding: "40px 24px", display: "flex", flexDirection: "column", gap: 4 },
  sidebarTitle: { color: "#94a3b8", fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 20 },
  stepItem: { display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 8, color: "#94a3b8", fontSize: 14 },
  stepActive: { background: "#334155", color: "#f1f5f9", fontWeight: 600 },
  stepDone: { color: "#4ade80" },
  stepDot: { width: 22, height: 22, borderRadius: "50%", background: "#334155", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, flexShrink: 0 },
  content: { flex: 1, padding: "60px 80px", maxWidth: 640 },
  h1: { fontSize: 28, fontWeight: 700, color: "#0f172a", marginBottom: 12, marginTop: 0 },
  body: { color: "#475569", lineHeight: 1.7, marginBottom: 20, fontSize: 15 },
  list: { color: "#475569", lineHeight: 2, paddingLeft: 24, marginBottom: 20 },
  code: { background: "#f1f5f9", padding: "2px 6px", borderRadius: 4, fontFamily: "monospace", fontSize: 13, color: "#0f172a" },
  link: { color: "#4f46e5", textDecoration: "underline" },
  fieldGroup: { marginBottom: 20 },
  label: { display: "block", fontWeight: 600, fontSize: 14, color: "#1e293b", marginBottom: 6 },
  input: { width: "100%", padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: 14, outline: "none", boxSizing: "border-box" },
  hint: { marginTop: 4, fontSize: 12, color: "#94a3b8" },
  row: { display: "flex", gap: 12, marginTop: 28 },
  btn: { padding: "10px 24px", background: "#4f46e5", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btnSecondary: { padding: "10px 24px", background: "#fff", color: "#475569", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  badge: { fontSize: 12, fontWeight: 600, background: "#f1f5f9", color: "#64748b", padding: "2px 8px", borderRadius: 20, verticalAlign: "middle", marginLeft: 8 },
  error: { color: "#dc2626", fontSize: 14, marginBottom: 12, background: "#fef2f2", padding: "10px 14px", borderRadius: 8 },
  doneWrap: { display: "flex", flexDirection: "column", alignItems: "flex-start", paddingTop: 20 },
  checkCircle: { width: 60, height: 60, borderRadius: "50%", background: "#dcfce7", color: "#16a34a", fontSize: 28, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24 },
};
