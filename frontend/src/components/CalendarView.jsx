import React from "react";
import { format, parseISO } from "date-fns";

const EVENT_COLORS = {
  "focus-block": "#4f46e5",
  meeting: "#0ea5e9",
  default: "#64748b",
};

function getEventColor(event) {
  if (event?.extendedProperties?.private?.type === "focus-block") return EVENT_COLORS["focus-block"];
  if ((event?.attendees?.length || 0) > 1) return EVENT_COLORS.meeting;
  return EVENT_COLORS.default;
}

function formatTime(dateTimeStr) {
  if (!dateTimeStr) return "";
  try {
    if (dateTimeStr.includes("T")) return format(parseISO(dateTimeStr), "h:mm a");
    return "";
  } catch {
    return dateTimeStr;
  }
}

function formatDate(dateTimeStr) {
  if (!dateTimeStr) return "";
  try {
    const d = dateTimeStr.includes("T") ? parseISO(dateTimeStr) : new Date(dateTimeStr + "T12:00:00");
    return format(d, "EEEE, MMMM d");
  } catch {
    return dateTimeStr;
  }
}

export default function CalendarView({ events }) {
  // Group events by date
  const byDate = {};
  for (const e of events) {
    const dateStr = (e.start?.dateTime || e.start?.date || "").split("T")[0];
    if (!byDate[dateStr]) byDate[dateStr] = [];
    byDate[dateStr].push(e);
  }

  const sortedDates = Object.keys(byDate).sort();

  if (sortedDates.length === 0) {
    return <div style={styles.empty}>No events in the next 7 days.</div>;
  }

  return (
    <div>
      {sortedDates.map((date) => (
        <div key={date} style={styles.dayGroup}>
          <div style={styles.dayHeader}>{formatDate(date + "T12:00:00")}</div>
          {byDate[date].map((event) => (
            <EventRow key={event.id} event={event} />
          ))}
        </div>
      ))}
    </div>
  );
}

function EventRow({ event }) {
  const isFocus = event?.extendedProperties?.private?.type === "focus-block";
  const color = getEventColor(event);
  const startTime = formatTime(event.start?.dateTime);
  const endTime = formatTime(event.end?.dateTime);
  const attendeeCount = event.attendees?.length || 0;

  return (
    <div style={{ ...styles.eventRow, borderLeft: `3px solid ${color}` }}>
      <div style={styles.eventTime}>
        {startTime}
        {endTime && <span style={styles.eventEndTime}> — {endTime}</span>}
      </div>
      <div style={styles.eventBody}>
        <div style={styles.eventTitle}>{event.summary || "Busy"}</div>
        <div style={styles.eventMeta}>
          {isFocus && <span style={styles.badge}>Focus Block</span>}
          {!isFocus && attendeeCount > 1 && <span style={{ ...styles.badge, background: "#e0f2fe", color: "#0369a1" }}>{attendeeCount} attendees</span>}
          {event.location && <span style={styles.location}>📍 {event.location.slice(0, 60)}</span>}
        </div>
      </div>
    </div>
  );
}

const styles = {
  dayGroup: { marginBottom: 24 },
  dayHeader: { fontSize: 13, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 },
  eventRow: { display: "flex", gap: 12, background: "#fff", borderRadius: 8, padding: "10px 14px", marginBottom: 6, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" },
  eventTime: { minWidth: 90, fontSize: 13, color: "#64748b", paddingTop: 1 },
  eventEndTime: { color: "#94a3b8" },
  eventBody: { flex: 1 },
  eventTitle: { fontSize: 14, fontWeight: 500, color: "#1e293b", marginBottom: 4 },
  eventMeta: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" },
  badge: { fontSize: 11, padding: "2px 8px", borderRadius: 10, background: "#ede9fe", color: "#6d28d9", fontWeight: 500 },
  location: { fontSize: 12, color: "#94a3b8" },
  empty: { padding: 40, textAlign: "center", color: "#94a3b8" },
};
