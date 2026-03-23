import React, { useState, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "";

export default function SchedulingLinks() {
  const [links, setLinks] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", duration_minutes: 30, buffer_before: 0, buffer_after: 0, rolling_days_available: 14, slug: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${API}/schedule/links`, { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setLinks(d.links || []));
  }, []);

  async function createLink(e) {
    e.preventDefault();
    setSaving(true);
    const resp = await fetch(`${API}/schedule/links`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(form),
    });
    const data = await resp.json();
    setLinks((prev) => [...prev, data]);
    setShowForm(false);
    setSaving(false);
    setForm({ title: "", duration_minutes: 30, buffer_before: 0, buffer_after: 0, rolling_days_available: 14, slug: "" });
  }

  async function deleteLink(id) {
    await fetch(`${API}/schedule/links/${id}`, { method: "DELETE", credentials: "include" });
    setLinks((prev) => prev.filter((l) => l.id !== id));
  }

  const baseUrl = window.location.origin;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Scheduling Links</h2>
        <button onClick={() => setShowForm(true)} style={styles.primaryBtn}>+ New Link</button>
      </div>

      {links.length === 0 && !showForm && (
        <div style={styles.empty}>
          <div style={styles.emptyIcon}>🔗</div>
          <p>No scheduling links yet. Create one to share your availability.</p>
        </div>
      )}

      {links.map((link) => (
        <div key={link.id} style={styles.card}>
          <div style={styles.cardHeader}>
            <div>
              <h3 style={styles.cardTitle}>{link.title}</h3>
              <span style={styles.cardMeta}>{link.duration_minutes} min · {link.rolling_days_available} days ahead</span>
            </div>
            <div style={styles.cardActions}>
              <a href={`/schedule/${link.slug}`} target="_blank" rel="noreferrer" style={styles.viewBtn}>View</a>
              <button onClick={() => {
                navigator.clipboard.writeText(`${baseUrl}/schedule/${link.slug}`);
              }} style={styles.copyBtn}>Copy Link</button>
              <button onClick={() => deleteLink(link.id)} style={styles.deleteBtn}>Delete</button>
            </div>
          </div>
          <div style={styles.slugRow}>
            <span style={styles.slugLabel}>URL:</span>
            <code style={styles.slugCode}>{baseUrl}/schedule/{link.slug}</code>
          </div>
        </div>
      ))}

      {showForm && (
        <div style={styles.formOverlay}>
          <div style={styles.formCard}>
            <h3 style={styles.formTitle}>New Scheduling Link</h3>
            <form onSubmit={createLink} style={styles.form}>
              <Field label="Title" required>
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} style={styles.input} placeholder="e.g. 30-min Intro Call" required />
              </Field>
              <Field label="Duration (minutes)">
                <input type="number" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: +e.target.value })} style={styles.input} min={15} />
              </Field>
              <Field label="Buffer before (min)">
                <input type="number" value={form.buffer_before} onChange={(e) => setForm({ ...form, buffer_before: +e.target.value })} style={styles.input} min={0} />
              </Field>
              <Field label="Buffer after (min)">
                <input type="number" value={form.buffer_after} onChange={(e) => setForm({ ...form, buffer_after: +e.target.value })} style={styles.input} min={0} />
              </Field>
              <Field label="Days available ahead">
                <input type="number" value={form.rolling_days_available} onChange={(e) => setForm({ ...form, rolling_days_available: +e.target.value })} style={styles.input} min={1} />
              </Field>
              <Field label="Custom slug (optional)">
                <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} style={styles.input} placeholder="e.g. jaimin-intro" />
              </Field>
              <div style={styles.formActions}>
                <button type="button" onClick={() => setShowForm(false)} style={styles.cancelBtn}>Cancel</button>
                <button type="submit" disabled={saving} style={styles.primaryBtn}>{saving ? "Creating..." : "Create Link"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, children, required }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#475569", marginBottom: 6 }}>
        {label}{required && <span style={{ color: "#ef4444" }}> *</span>}
      </label>
      {children}
    </div>
  );
}

const styles = {
  container: { maxWidth: 800, margin: "0 auto", padding: "32px 24px" },
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 },
  title: { fontSize: 24, fontWeight: 700 },
  primaryBtn: { padding: "10px 20px", background: "#4f46e5", color: "#fff", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer", fontSize: 14 },
  empty: { background: "#f8fafc", borderRadius: 12, padding: 40, textAlign: "center", color: "#64748b" },
  emptyIcon: { fontSize: 32, marginBottom: 8 },
  card: { background: "#fff", borderRadius: 12, padding: 20, marginBottom: 12, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" },
  cardHeader: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: 600 },
  cardMeta: { fontSize: 13, color: "#64748b" },
  cardActions: { display: "flex", gap: 8 },
  viewBtn: { padding: "6px 14px", borderRadius: 6, border: "1px solid #e2e8f0", textDecoration: "none", color: "#4f46e5", fontSize: 13, fontWeight: 500 },
  copyBtn: { padding: "6px 14px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontSize: 13 },
  deleteBtn: { padding: "6px 14px", borderRadius: 6, border: "1px solid #fee2e2", background: "#fff", color: "#ef4444", cursor: "pointer", fontSize: 13 },
  slugRow: { display: "flex", alignItems: "center", gap: 8 },
  slugLabel: { fontSize: 12, color: "#94a3b8" },
  slugCode: { fontSize: 12, background: "#f1f5f9", padding: "2px 8px", borderRadius: 4, color: "#475569" },
  formOverlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 },
  formCard: { background: "#fff", borderRadius: 16, padding: 32, width: 460, maxWidth: "90vw" },
  formTitle: { fontSize: 18, fontWeight: 700, marginBottom: 24 },
  form: {},
  input: { width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 14 },
  formActions: { display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 },
  cancelBtn: { padding: "8px 16px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontSize: 14 },
};
