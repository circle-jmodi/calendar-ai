import React from "react";
import { format, parseISO } from "date-fns";

export default function MeetingSuggestion({ suggestion, onAccept }) {
  const currentStart = suggestion.current_start ? parseISO(suggestion.current_start) : null;
  const suggestedStart = suggestion.suggested_start ? parseISO(suggestion.suggested_start) : null;

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.badge}>Move suggestion</span>
      </div>
      <div style={styles.timing}>
        {currentStart && (
          <div style={styles.timeRow}>
            <span style={styles.timeLabel}>Now:</span>
            <span style={styles.timeOld}>{format(currentStart, "EEE, MMM d 'at' h:mm a")}</span>
          </div>
        )}
        {suggestedStart && (
          <div style={styles.timeRow}>
            <span style={styles.timeLabel}>Suggested:</span>
            <span style={styles.timeNew}>{format(suggestedStart, "EEE, MMM d 'at' h:mm a")}</span>
          </div>
        )}
      </div>
      <p style={styles.reasoning}>{suggestion.reasoning}</p>
      <button onClick={onAccept} style={styles.acceptBtn}>Accept & Move</button>
    </div>
  );
}

const styles = {
  card: { background: "#fff", borderRadius: 10, padding: "14px 16px", marginBottom: 8, border: "1px solid #e2e8f0" },
  header: { marginBottom: 8 },
  badge: { fontSize: 11, padding: "2px 8px", borderRadius: 10, background: "#fef3c7", color: "#92400e", fontWeight: 500 },
  timing: { display: "flex", flexDirection: "column", gap: 4, marginBottom: 8 },
  timeRow: { display: "flex", gap: 8, alignItems: "center" },
  timeLabel: { fontSize: 12, color: "#94a3b8", width: 68, flexShrink: 0 },
  timeOld: { fontSize: 13, color: "#64748b", textDecoration: "line-through" },
  timeNew: { fontSize: 13, color: "#059669", fontWeight: 500 },
  reasoning: { fontSize: 12, color: "#64748b", lineHeight: 1.5, marginBottom: 12 },
  acceptBtn: { padding: "6px 14px", background: "#10b981", color: "#fff", border: "none", borderRadius: 6, fontWeight: 500, cursor: "pointer", fontSize: 13 },
};
