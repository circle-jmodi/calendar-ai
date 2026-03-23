import React, { useState, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "";

const TIMEZONES = ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "UTC", "Europe/London", "Europe/Paris", "Asia/Kolkata", "Asia/Tokyo"];
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function Preferences() {
  const [prefs, setPrefs] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`${API}/preferences`, { credentials: "include" })
      .then((r) => r.json())
      .then(setPrefs);
  }, []);

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    await fetch(`${API}/preferences`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(prefs),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function update(field, value) {
    setPrefs((p) => ({ ...p, [field]: value }));
  }

  function toggleDay(list, field, day) {
    const current = list || [];
    const next = current.includes(day) ? current.filter((d) => d !== day) : [...current, day];
    update(field, next.sort());
  }

  if (!prefs) return <div style={styles.loading}>Loading preferences...</div>;

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Preferences</h2>
      <form onSubmit={save}>
        <Section title="Work Hours">
          <Row label="Timezone">
            <select value={prefs.work_timezone} onChange={(e) => update("work_timezone", e.target.value)} style={styles.select}>
              {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
            </select>
          </Row>
          <Row label="Work Hours">
            <input type="number" min={0} max={23} value={prefs.work_start_hour} onChange={(e) => update("work_start_hour", +e.target.value)} style={styles.numInput} />
            <span style={styles.sep}>to</span>
            <input type="number" min={0} max={23} value={prefs.work_end_hour} onChange={(e) => update("work_end_hour", +e.target.value)} style={styles.numInput} />
          </Row>
          <Row label="Work Days">
            <DayPicker days={prefs.work_days || [0,1,2,3,4]} onToggle={(d) => toggleDay(prefs.work_days, "work_days", d)} />
          </Row>
        </Section>

        <Section title="Focus Time">
          <Row label="Hours per day">
            <input type="number" min={1} max={8} value={prefs.focus_hours_per_day} onChange={(e) => update("focus_hours_per_day", +e.target.value)} style={styles.numInput} />
          </Row>
          <Row label="Days per week">
            <input type="number" min={1} max={7} value={prefs.focus_days_per_week} onChange={(e) => update("focus_days_per_week", +e.target.value)} style={styles.numInput} />
          </Row>
          <Row label="Preferred time">
            <select value={prefs.focus_preferred_time} onChange={(e) => update("focus_preferred_time", e.target.value)} style={styles.select}>
              <option value="morning">Morning</option>
              <option value="afternoon">Afternoon</option>
            </select>
          </Row>
          <Row label="Block length (min)">
            <input type="number" min={15} value={prefs.focus_min_block_minutes} onChange={(e) => update("focus_min_block_minutes", +e.target.value)} style={styles.numInput} />
            <span style={styles.sep}>to</span>
            <input type="number" min={15} value={prefs.focus_max_block_minutes} onChange={(e) => update("focus_max_block_minutes", +e.target.value)} style={styles.numInput} />
          </Row>
        </Section>

        <Section title="Meeting Rules">
          <Row label="Buffer between meetings (min)">
            <input type="number" min={0} max={60} value={prefs.meeting_buffer_minutes} onChange={(e) => update("meeting_buffer_minutes", +e.target.value)} style={styles.numInput} />
          </Row>
          <Row label="No-meeting days">
            <DayPicker days={prefs.no_meeting_days || []} onToggle={(d) => toggleDay(prefs.no_meeting_days, "no_meeting_days", d)} />
          </Row>
          <Row label="Auto-move meetings">
            <Toggle value={prefs.allow_auto_move_meetings} onChange={(v) => update("allow_auto_move_meetings", v)} />
            <span style={styles.hint}>Allow AI to reschedule meetings (sends updates to attendees)</span>
          </Row>
        </Section>

        <Section title="Slack Status">
          <Row label="Enable status sync">
            <Toggle value={prefs.slack_status_sync_enabled} onChange={(v) => update("slack_status_sync_enabled", v)} />
          </Row>
          <Row label="Focus status text">
            <input value={prefs.slack_focus_status_text} onChange={(e) => update("slack_focus_status_text", e.target.value)} style={styles.textInput} />
          </Row>
          <Row label="Focus status emoji">
            <input value={prefs.slack_focus_status_emoji} onChange={(e) => update("slack_focus_status_emoji", e.target.value)} style={styles.textInput} placeholder=":dart:" />
          </Row>
        </Section>

        <Section title="Gong Recording">
          <Row label="Auto-record Teams meetings">
            <Toggle value={prefs.gong_auto_record_enabled} onChange={(v) => update("gong_auto_record_enabled", v)} />
            <span style={styles.hint}>Automatically adds circle@assistant.gong.io to Microsoft Teams meetings</span>
          </Row>
        </Section>

        <div style={styles.actions}>
          <button type="submit" disabled={saving} style={styles.saveBtn}>
            {saving ? "Saving..." : saved ? "Saved!" : "Save Preferences"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={styles.section}>
      <h3 style={styles.sectionTitle}>{title}</h3>
      <div style={styles.sectionBody}>{children}</div>
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div style={styles.row}>
      <label style={styles.label}>{label}</label>
      <div style={styles.rowValue}>{children}</div>
    </div>
  );
}

function DayPicker({ days, onToggle }) {
  return (
    <div style={styles.dayPicker}>
      {DAYS.map((d, i) => (
        <button
          key={i} type="button"
          onClick={() => onToggle(i)}
          style={{ ...styles.dayBtn, ...(days.includes(i) ? styles.dayBtnActive : {}) }}
        >
          {d}
        </button>
      ))}
    </div>
  );
}

function Toggle({ value, onChange }) {
  return (
    <div onClick={() => onChange(!value)} style={{ ...styles.toggle, ...(value ? styles.toggleOn : {}) }}>
      <div style={{ ...styles.toggleKnob, ...(value ? styles.toggleKnobOn : {}) }} />
    </div>
  );
}

const styles = {
  container: { maxWidth: 720, margin: "0 auto", padding: "32px 24px" },
  title: { fontSize: 24, fontWeight: 700, marginBottom: 24 },
  loading: { padding: 40, color: "#64748b" },
  section: { background: "#fff", borderRadius: 12, padding: 24, marginBottom: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" },
  sectionTitle: { fontSize: 16, fontWeight: 600, color: "#1e293b", marginBottom: 16 },
  sectionBody: { display: "flex", flexDirection: "column", gap: 14 },
  row: { display: "flex", alignItems: "center", gap: 12 },
  label: { width: 220, fontSize: 14, color: "#475569", fontWeight: 500 },
  rowValue: { display: "flex", alignItems: "center", gap: 8 },
  select: { padding: "6px 10px", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 14 },
  numInput: { width: 70, padding: "6px 10px", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 14 },
  textInput: { padding: "6px 10px", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 14, width: 200 },
  sep: { color: "#94a3b8", fontSize: 13 },
  hint: { fontSize: 12, color: "#94a3b8" },
  dayPicker: { display: "flex", gap: 6 },
  dayBtn: { padding: "4px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", fontSize: 13, cursor: "pointer", color: "#64748b" },
  dayBtnActive: { background: "#4f46e5", color: "#fff", border: "1px solid #4f46e5" },
  toggle: { width: 40, height: 22, borderRadius: 11, background: "#e2e8f0", cursor: "pointer", position: "relative", transition: "background 0.2s" },
  toggleOn: { background: "#4f46e5" },
  toggleKnob: { position: "absolute", top: 3, left: 3, width: 16, height: 16, borderRadius: "50%", background: "#fff", transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" },
  toggleKnobOn: { left: 21 },
  actions: { marginTop: 8 },
  saveBtn: { padding: "10px 24px", background: "#4f46e5", color: "#fff", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer", fontSize: 14 },
};
