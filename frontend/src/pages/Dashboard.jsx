import React, { useState, useEffect } from "react";
import CalendarView from "../components/CalendarView";
import FocusBlockCard from "../components/FocusBlockCard";
import MeetingSuggestion from "../components/MeetingSuggestion";

const API = import.meta.env.VITE_API_URL || "";

export default function Dashboard() {
  const [events, setEvents] = useState([]);
  const [focusBlocks, setFocusBlocks] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [evResp, fbResp] = await Promise.all([
        fetch(`${API}/calendar/events?days=7`, { credentials: "include" }),
        fetch(`${API}/calendar/focus-blocks?days=7`, { credentials: "include" }),
      ]);
      if (evResp.ok) {
        const d = await evResp.json();
        setEvents(d.events || []);
      }
      if (fbResp.ok) {
        const d = await fbResp.json();
        setFocusBlocks(d.focus_blocks || []);
      }
    } finally {
      setLoading(false);
    }
  }

  async function runOptimization() {
    setOptimizing(true);
    setMessage("");
    try {
      const resp = await fetch(`${API}/optimize/run`, { method: "POST", credentials: "include" });
      const data = await resp.json();
      setMessage(data.summary || "Optimization complete!");
      if (data.meeting_suggestions) setSuggestions(data.meeting_suggestions);
      await loadData();
    } catch (e) {
      setMessage("Optimization failed. Check that your Google Calendar is connected.");
    } finally {
      setOptimizing(false);
    }
  }

  async function acceptSuggestion(eventId, suggestedStart) {
    await fetch(`${API}/calendar/suggestions/${eventId}/accept?suggested_start=${encodeURIComponent(suggestedStart)}`, {
      method: "POST",
      credentials: "include",
    });
    setSuggestions((prev) => prev.filter((s) => s.event_id !== eventId));
    await loadData();
  }

  if (loading) return <div style={styles.loading}>Loading your calendar...</div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>This Week</h2>
          <p style={styles.subtitle}>Next 7 days · {events.length} events · {focusBlocks.length} focus blocks</p>
        </div>
        <button onClick={runOptimization} disabled={optimizing} style={styles.primaryBtn}>
          {optimizing ? "Optimizing..." : "✨ Optimize with AI"}
        </button>
      </div>

      {message && <div style={styles.banner}>{message}</div>}

      <div style={styles.grid}>
        <div style={styles.mainCol}>
          <CalendarView events={events} />
        </div>

        <div style={styles.sideCol}>
          {focusBlocks.length > 0 && (
            <section>
              <h3 style={styles.sectionTitle}>Focus Blocks</h3>
              {focusBlocks.map((b) => <FocusBlockCard key={b.id} block={b} />)}
            </section>
          )}

          {suggestions.length > 0 && (
            <section style={{ marginTop: 24 }}>
              <h3 style={styles.sectionTitle}>Meeting Suggestions</h3>
              <p style={styles.hint}>Claude suggests these moves to protect your focus time.</p>
              {suggestions.map((s) => (
                <MeetingSuggestion
                  key={s.event_id}
                  suggestion={s}
                  onAccept={() => acceptSuggestion(s.event_id, s.suggested_start)}
                />
              ))}
            </section>
          )}

          {focusBlocks.length === 0 && suggestions.length === 0 && (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>🎯</div>
              <p>Click "Optimize with AI" to create focus blocks and get meeting suggestions.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: 1100, margin: "0 auto", padding: "32px 24px" },
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 },
  title: { fontSize: 24, fontWeight: 700, color: "#1e293b" },
  subtitle: { color: "#64748b", marginTop: 4, fontSize: 14 },
  primaryBtn: { padding: "10px 20px", background: "#4f46e5", color: "#fff", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer", fontSize: 14 },
  banner: { background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, padding: "12px 16px", marginBottom: 20, color: "#1d4ed8", fontSize: 14 },
  grid: { display: "grid", gridTemplateColumns: "1fr 320px", gap: 24 },
  mainCol: {},
  sideCol: {},
  sectionTitle: { fontSize: 16, fontWeight: 600, color: "#1e293b", marginBottom: 12 },
  hint: { fontSize: 13, color: "#64748b", marginBottom: 12 },
  emptyState: { background: "#f8fafc", borderRadius: 12, padding: 24, textAlign: "center", color: "#64748b", fontSize: 14 },
  emptyIcon: { fontSize: 32, marginBottom: 8 },
  loading: { display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300, color: "#64748b" },
};
