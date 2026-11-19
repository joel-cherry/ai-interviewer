import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type InterviewSession, type JobDescription, type MatchResult, type ResumeDocument } from "../api";
import { useSession } from "../session";
import { Card, Chips, ErrorBanner, Spinner, errorMessage, formatDate, scoreTone } from "../ui";

const ACCEPT = ".pdf,.docx,.txt,.md";

function UploadButton({ label, onFile, busy }: { label: string; onFile: (f: File) => void; busy: boolean }) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={ref}
        type="file"
        accept={ACCEPT}
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          if (file) onFile(file);
        }}
      />
      <button className="btn btn-sm" disabled={busy} onClick={() => ref.current?.click()}>
        {busy ? "Uploading…" : label}
      </button>
    </>
  );
}

export default function Dashboard() {
  const { session } = useSession();
  const profileId = session!.profileId;
  const navigate = useNavigate();

  const [resumes, setResumes] = useState<ResumeDocument[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [interviews, setInterviews] = useState<InterviewSession[]>([]);
  const [matches, setMatches] = useState<Record<string, MatchResult>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<"resume" | "job" | null>(null);

  const [title, setTitle] = useState("Practice interview");
  const [jobId, setJobId] = useState("");
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, j, i] = await Promise.all([api.listResumes(profileId), api.listJobs(profileId), api.listInterviews(profileId)]);
      setResumes(r);
      setJobs(j);
      setInterviews([...i].sort((a, b) => b.created_at.localeCompare(a.created_at)));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [profileId]);

  useEffect(() => {
    load();
  }, [load]);

  async function uploadResume(file: File) {
    setUploading("resume");
    setError(null);
    try {
      const doc = await api.uploadResume(profileId, file);
      setResumes((prev) => [...prev, doc]);
      setMatches({});
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setUploading(null);
    }
  }

  async function uploadJob(file: File) {
    setUploading("job");
    setError(null);
    try {
      const doc = await api.uploadJob(profileId, file);
      setJobs((prev) => [...prev, doc]);
      setJobId(doc.id);
      setTitle(`${doc.title} interview`.slice(0, 255));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setUploading(null);
    }
  }

  async function checkMatch(id: string) {
    try {
      const result = await api.matchJob(profileId, id);
      setMatches((prev) => ({ ...prev, [id]: result }));
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function start(e: FormEvent) {
    e.preventDefault();
    setStarting(true);
    setError(null);
    try {
      const res = await api.startInterview(profileId, title.trim() || "Practice interview", jobId || undefined);
      navigate(`/interview/${res.session_id}`);
    } catch (err) {
      setError(errorMessage(err));
      setStarting(false);
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this interview and its report?")) return;
    try {
      await api.deleteInterview(id);
      setInterviews((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  if (loading) return <Spinner text="Loading your workspace…" />;

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1>Welcome, {session!.name.split(" ")[0]}</h1>
          <p className="muted">Add context, start a session, and review your progress.</p>
        </div>
      </div>

      <ErrorBanner error={error} onRetry={load} />

      <Card title="Start a new interview">
        <form className="start-form" onSubmit={start}>
          <label>
            Session title
            <input value={title} maxLength={255} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            Target role
            <select value={jobId} onChange={(e) => setJobId(e.target.value)}>
              <option value="">General (no job description)</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </label>
          <button className="btn btn-primary" disabled={starting}>
            {starting ? "Starting…" : "Start interview"}
          </button>
        </form>
        {!resumes.length && (
          <p className="muted small">Tip: upload your resume first so questions can focus on your skills.</p>
        )}
      </Card>

      <div className="grid-2">
        <Card title="Resume" action={<UploadButton label="Upload" busy={uploading === "resume"} onFile={uploadResume} />}>
          {resumes.length === 0 ? (
            <p className="muted">PDF, DOCX or TXT, up to 5 MB. We extract your skills and experience.</p>
          ) : (
            <ul className="list">
              {resumes.map((r) => (
                <li key={r.id}>
                  <div className="list-title">
                    <strong>{r.file_name}</strong>
                    {r.experience_years != null && <span className="muted small">{r.experience_years} yrs experience</span>}
                  </div>
                  <Chips items={r.skills} />
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Job descriptions" action={<UploadButton label="Upload" busy={uploading === "job"} onFile={uploadJob} />}>
          {jobs.length === 0 ? (
            <p className="muted">Add a job description to tailor questions and see how your skills match.</p>
          ) : (
            <ul className="list">
              {jobs.map((j) => {
                const m = matches[j.id];
                // Backend returns a 0-1 fraction; accept 0-100 too in case that changes.
                const matchPct = m ? Math.round(m.overall_score <= 1 ? m.overall_score * 100 : m.overall_score) : 0;
                return (
                  <li key={j.id}>
                    <div className="list-title">
                      <strong>{j.title}</strong>
                      <button className="btn btn-ghost btn-sm" onClick={() => checkMatch(j.id)} disabled={!resumes.length} title={resumes.length ? "" : "Upload a resume first"}>
                        {m ? "Recheck" : "Check match"}
                      </button>
                    </div>
                    {m ? (
                      <div className="match">
                        <span className={`pill tone-${scoreTone(matchPct)}`}>{matchPct}% skill match</span>
                        <div className="small">Matched</div>
                        <Chips items={m.matched_skills} tone="good" />
                        <div className="small">Missing</div>
                        <Chips items={m.missing_skills} tone="low" />
                      </div>
                    ) : (
                      <Chips items={j.required_skills} />
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>
      </div>

      <Card title="Your interviews">
        {interviews.length === 0 ? (
          <p className="muted">No interviews yet. Start one above.</p>
        ) : (
          <ul className="list">
            {interviews.map((i) => {
              const done = i.status === "completed";
              return (
                <li key={i.id} className="list-row">
                  <div>
                    <strong>{i.title}</strong>
                    <div className="muted small">
                      {formatDate(i.created_at)} · {done ? "Completed" : `Question ${i.current_turn} of ${i.max_turns}`}
                    </div>
                  </div>
                  <div className="row-actions">
                    <Link className="btn btn-sm btn-primary" to={done ? `/report/${i.id}` : `/interview/${i.id}`}>
                      {done ? "View report" : "Continue"}
                    </Link>
                    <button className="btn btn-ghost btn-sm" onClick={() => remove(i.id)} aria-label={`Delete ${i.title}`}>
                      Delete
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
