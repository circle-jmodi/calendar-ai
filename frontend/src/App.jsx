import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Preferences from "./pages/Preferences";
import SchedulingLinks from "./pages/SchedulingLinks";
import BookingPage from "./pages/BookingPage";
import SetupWizard from "./pages/SetupWizard";

const API = import.meta.env.VITE_API_URL || "";

export const UserContext = createContext(null);

export function useUser() {
  return useContext(UserContext);
}

function NavBar({ user, onLogout }) {
  return (
    <nav style={styles.nav}>
      <Link to="/dashboard" style={styles.brand}>Calendar AI</Link>
      <div style={styles.navLinks}>
        <Link to="/dashboard" style={styles.navLink}>Dashboard</Link>
        <Link to="/preferences" style={styles.navLink}>Preferences</Link>
        <Link to="/scheduling" style={styles.navLink}>Scheduling Links</Link>
      </div>
      <div style={styles.navUser}>
        <span style={styles.userEmail}>{user?.email}</span>
        <button onClick={onLogout} style={styles.btnSmall}>Sign Out</button>
      </div>
    </nav>
  );
}

function ProtectedRoute({ user, children }) {
  if (!user) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const [setupComplete, setSetupComplete] = useState(null); // null = loading
  const [user, setUser] = useState(undefined); // undefined = loading

  useEffect(() => {
    fetch(`${API}/setup/status`)
      .then((r) => r.json())
      .then((d) => setSetupComplete(d.complete))
      .catch(() => setSetupComplete(true)); // if endpoint fails, don't block
  }, []);

  useEffect(() => {
    if (setupComplete !== true) return;
    fetch(`${API}/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setUser(data))
      .catch(() => setUser(null));
  }, [setupComplete]);

  const handleLogout = async () => {
    await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
    setUser(null);
  };

  if (setupComplete === null) {
    return <div style={styles.center}><div style={styles.spinner} /></div>;
  }

  if (setupComplete === false) {
    return <SetupWizard onComplete={() => window.location.reload()} />;
  }

  const loading = user === undefined;
  if (loading) {
    return <div style={styles.center}><div style={styles.spinner} /></div>;
  }

  return (
    <UserContext.Provider value={{ user, setUser }}>
      <BrowserRouter>
        {user && <NavBar user={user} onLogout={handleLogout} />}
        <Routes>
          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
          <Route path="/schedule/:slug" element={<BookingPage />} />
          <Route path="/dashboard" element={<ProtectedRoute user={user}><Dashboard /></ProtectedRoute>} />
          <Route path="/preferences" element={<ProtectedRoute user={user}><Preferences /></ProtectedRoute>} />
          <Route path="/scheduling" element={<ProtectedRoute user={user}><SchedulingLinks /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </UserContext.Provider>
  );
}

const styles = {
  nav: { display: "flex", alignItems: "center", padding: "12px 24px", background: "#fff", borderBottom: "1px solid #e2e8f0", gap: 24 },
  brand: { fontWeight: 700, fontSize: 18, color: "#4f46e5", textDecoration: "none" },
  navLinks: { display: "flex", gap: 20, flex: 1 },
  navLink: { textDecoration: "none", color: "#64748b", fontSize: 14, fontWeight: 500 },
  navUser: { display: "flex", alignItems: "center", gap: 12 },
  userEmail: { fontSize: 14, color: "#64748b" },
  btnSmall: { padding: "6px 14px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontSize: 13 },
  center: { display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" },
  spinner: { width: 32, height: 32, border: "3px solid #e2e8f0", borderTop: "3px solid #4f46e5", borderRadius: "50%", animation: "spin 1s linear infinite" },
};
