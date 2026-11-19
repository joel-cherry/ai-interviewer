import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useSession } from "../session";
import { ErrorBanner, errorMessage } from "../ui";

export default function SignIn() {
  const { session, setSession } = useSession();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (session) return <Navigate to="/dashboard" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await api.signIn(email.trim(), name.trim());
      const profiles = await api.listProfiles(user.id);
      const profile =
        profiles[0] ??
        (await api.createProfile({
          user_id: user.id,
          full_name: name.trim(),
          current_role: role.trim() || null,
        }));
      setSession({ userId: user.id, profileId: profile.id, name: profile.full_name, email: user.email });
      navigate("/dashboard");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Interview practice</p>
        <h1>Rehearse the interview before it counts.</h1>
        <p className="lead">
          Upload your resume and a job description, then answer adaptive questions by typing or speaking. You get a
          rubric-based report with strengths, gaps, and what to improve.
        </p>
        <ul className="steps">
          <li><span>1</span>Add your resume and target role</li>
          <li><span>2</span>Answer 5 adaptive questions by text or voice</li>
          <li><span>3</span>Review scores and coaching feedback</li>
        </ul>
      </div>

      <form className="card form" onSubmit={submit}>
        <h2>Get started</h2>
        <p className="muted small">No password: your email just keeps your interviews together.</p>
        <label>
          Full name
          <input required maxLength={255} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
        </label>
        <label>
          Email
          <input required type="email" maxLength={255} value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        </label>
        <label>
          Current role <span className="muted">(optional)</span>
          <input maxLength={255} value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Final-year CS student" />
        </label>
        <ErrorBanner error={error} />
        <button className="btn btn-primary" disabled={busy}>
          {busy ? "Signing in…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
