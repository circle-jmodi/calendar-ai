import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { format, parseISO } from "date-fns";

const API = import.meta.env.VITE_API_URL || "";

export default function BookingPage() {
  const { slug } = useParams();
  const [linkInfo, setLinkInfo] = useState(null);
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [form, setForm] = useState({ name: "", email: "" });
  const [booking, setBooking] = useState(false);
  const [booked, setBooked] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/schedule/${slug}`).then((r) => r.json()),
      fetch(`${API}/schedule/${slug}/availability`).then((r) => r.json()),
    ]).then(([info, avail]) => {
      setLinkInfo(info);
      setSlots(avail.slots || []);
      setLoading(false);
    }).catch(() => {
      setError("Could not load scheduling link.");
      setLoading(false);
    });
  }, [slug]);

  // Group slots by date
  const slotsByDate = slots.reduce((acc, slot) => {
    const date = slot.start.split("T")[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(slot);
    return acc;
  }, {});

  async function handleBook(e) {
    e.preventDefault();
    if (!selectedSlot) return;
    setBooking(true);
    setError("");
    try {
      const resp = await fetch(`${API}/schedule/${slug}/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_start: selectedSlot.start,
          slot_end: selectedSlot.end,
          name: form.name,
          email: form.email,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Booking failed");
      }
      setBooked(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBooking(false);
    }
  }

  if (loading) return <div style={styles.center}>Loading...</div>;
  if (error && !linkInfo) return <div style={styles.center}>{error}</div>;

  if (booked) {
    return (
      <div style={styles.center}>
        <div style={styles.successCard}>
          <div style={styles.successIcon}>✅</div>
          <h2 style={styles.successTitle}>Booking Confirmed!</h2>
          <p style={styles.successText}>
            You'll receive a calendar invite at <strong>{form.email}</strong>.
          </p>
          {selectedSlot && (
            <p style={styles.successTime}>
              {format(parseISO(selectedSlot.start), "EEEE, MMMM d 'at' h:mm a")}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>{linkInfo?.title}</h1>
          <span style={styles.duration}>{linkInfo?.duration_minutes} minutes</span>
        </div>

        <div style={styles.layout}>
          {/* Slot picker */}
          <div style={styles.slotPanel}>
            <h3 style={styles.panelTitle}>Select a time</h3>
            {Object.keys(slotsByDate).length === 0 && (
              <p style={styles.noSlots}>No available slots found.</p>
            )}
            {Object.entries(slotsByDate).slice(0, 14).map(([date, dateSlots]) => (
              <div key={date} style={styles.dateGroup}>
                <div style={styles.dateLabel}>
                  {format(new Date(date + "T12:00:00"), "EEEE, MMMM d")}
                </div>
                <div style={styles.slotGrid}>
                  {dateSlots.map((slot) => (
                    <button
                      key={slot.start}
                      onClick={() => setSelectedSlot(slot)}
                      style={{
                        ...styles.slotBtn,
                        ...(selectedSlot?.start === slot.start ? styles.slotBtnSelected : {}),
                      }}
                    >
                      {format(parseISO(slot.start), "h:mm a")}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Booking form */}
          {selectedSlot && (
            <div style={styles.formPanel}>
              <h3 style={styles.panelTitle}>Your details</h3>
              <p style={styles.selectedTime}>
                {format(parseISO(selectedSlot.start), "EEEE, MMMM d 'at' h:mm a")}
              </p>
              <form onSubmit={handleBook} style={styles.form}>
                <div style={styles.field}>
                  <label style={styles.fieldLabel}>Name</label>
                  <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={styles.input} required placeholder="Your name" />
                </div>
                <div style={styles.field}>
                  <label style={styles.fieldLabel}>Email</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={styles.input} required placeholder="you@example.com" />
                </div>
                {error && <p style={styles.error}>{error}</p>}
                <button type="submit" disabled={booking} style={styles.bookBtn}>
                  {booking ? "Booking..." : "Confirm Booking"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: { background: "#f8fafc", minHeight: "100vh", padding: "40px 24px" },
  center: { display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" },
  container: { maxWidth: 840, margin: "0 auto" },
  header: { textAlign: "center", marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 700, color: "#1e293b" },
  duration: { display: "inline-block", marginTop: 8, background: "#eff6ff", color: "#3b82f6", padding: "4px 12px", borderRadius: 20, fontSize: 13, fontWeight: 500 },
  layout: { display: "grid", gridTemplateColumns: "1fr 300px", gap: 24, alignItems: "start" },
  slotPanel: { background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" },
  formPanel: { background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" },
  panelTitle: { fontSize: 16, fontWeight: 600, marginBottom: 16 },
  noSlots: { color: "#94a3b8", fontSize: 14 },
  dateGroup: { marginBottom: 20 },
  dateLabel: { fontSize: 13, fontWeight: 600, color: "#64748b", marginBottom: 8 },
  slotGrid: { display: "flex", flexWrap: "wrap", gap: 8 },
  slotBtn: { padding: "8px 14px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontSize: 13, color: "#1e293b" },
  slotBtnSelected: { background: "#4f46e5", color: "#fff", border: "1px solid #4f46e5" },
  selectedTime: { fontSize: 14, fontWeight: 500, color: "#4f46e5", marginBottom: 20 },
  form: {},
  field: { marginBottom: 16 },
  fieldLabel: { display: "block", fontSize: 13, fontWeight: 500, color: "#475569", marginBottom: 6 },
  input: { width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 14 },
  error: { color: "#ef4444", fontSize: 13, marginBottom: 12 },
  bookBtn: { width: "100%", padding: "10px", background: "#4f46e5", color: "#fff", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer", fontSize: 14 },
  successCard: { background: "#fff", borderRadius: 16, padding: 48, textAlign: "center", boxShadow: "0 4px 24px rgba(0,0,0,0.08)", maxWidth: 400 },
  successIcon: { fontSize: 48, marginBottom: 16 },
  successTitle: { fontSize: 24, fontWeight: 700, marginBottom: 12 },
  successText: { color: "#64748b", fontSize: 15, marginBottom: 8 },
  successTime: { color: "#4f46e5", fontWeight: 500 },
};
