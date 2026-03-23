import React from "react";
import { format, parseISO, differenceInMinutes } from "date-fns";

export default function FocusBlockCard({ block }) {
  const start = block.start?.dateTime ? parseISO(block.start.dateTime) : null;
  const end = block.end?.dateTime ? parseISO(block.end.dateTime) : null;
  const duration = start && end ? differenceInMinutes(end, start) : null;

  return (
    <div style={styles.card}>
      <div style={styles.icon}>🎯</div>
      <div style={styles.body}>
        <div style={styles.title}>{block.summary || "Focus Time"}</div>
        {start && (
          <div style={styles.time}>
            {format(start, "EEE, MMM d")} · {format(start, "h:mm a")} – {end ? format(end, "h:mm a") : ""}
            {duration !== null && <span style={styles.duration}> ({duration} min)</span>}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  card: { display: "flex", alignItems: "flex-start", gap: 12, background: "#ede9fe", borderRadius: 10, padding: "12px 14px", marginBottom: 8 },
  icon: { fontSize: 20, marginTop: 1 },
  body: { flex: 1 },
  title: { fontSize: 14, fontWeight: 600, color: "#4c1d95" },
  time: { fontSize: 12, color: "#6d28d9", marginTop: 2 },
  duration: { color: "#7c3aed" },
};
