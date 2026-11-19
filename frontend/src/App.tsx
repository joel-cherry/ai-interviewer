import type { ReactNode } from "react";
import { HashRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { isEmbedded } from "./embed";
import { SessionProvider, useSession } from "./session";
import SignIn from "./pages/SignIn";
import Dashboard from "./pages/Dashboard";
import Interview from "./pages/Interview";
import Report from "./pages/Report";

function RequireSession({ children }: { children: ReactNode }) {
  const { session } = useSession();
  return session ? <>{children}</> : <Navigate to="/" replace />;
}

function Header() {
  const { session, setSession } = useSession();
  return (
    <header className="topbar">
      <Link to={session ? "/dashboard" : "/"} className="brand">
        <span className="brand-mark" aria-hidden>
          ◆
        </span>
        AI Mock Interviewer
      </Link>
      {session && (
        <nav className="topbar-actions">
          <span className="muted hide-sm">{session.name}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setSession(null)}>
            Sign out
          </button>
        </nav>
      )}
    </header>
  );
}

export default function App() {
  return (
    <SessionProvider>
      {/* HashRouter: deep links work on any static host, sub-folder, or iframe without server rewrites. */}
      <HashRouter>
        <div className="app">
          <Header />
          <main className="container">
            <Routes>
              <Route path="/" element={<SignIn />} />
              <Route path="/dashboard" element={<RequireSession><Dashboard /></RequireSession>} />
              <Route path="/interview/:id" element={<RequireSession><Interview /></RequireSession>} />
              <Route path="/report/:id" element={<RequireSession><Report /></RequireSession>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          {!isEmbedded && (
            <footer className="footer muted">
              Coaching tool. Scores are rubric-based practice feedback, not hiring decisions.
            </footer>
          )}
        </div>
      </HashRouter>
    </SessionProvider>
  );
}
