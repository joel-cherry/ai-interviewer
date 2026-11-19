import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type InterviewSession, type Recommendation, type Report as ReportData, type SpeechAnalysis } from "../api";
import { Bar, Card, ErrorBanner, ScoreRing, Spinner, errorMessage, formatDate, label, scoreTone } from "../ui";

const DIMENSIONS = ["technical_knowledge", "problem_solving", "communication", "role_fit", "confidence", "experience_relevance"] as const;

export default function Report() {
  const { id = "" } = useParams();
  const [report, setReport] = useState<ReportData | null>(null);
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [speech, setSpeech] = useState<SpeechAnalysis | null>(null);
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Report first: it creates the evaluation if missing, so the parallel calls below don't race to create it.
      const r = await api.report(id);
      const [recommendation, speechAnalysis, s] = await Promise.all([api.recommendation(id), api.speech(id), api.getInterview(id)]);
      setReport(r);
      setRec(recommendation);
      setSpeech(speechAnalysis);
      setSession(s);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  function download() {
    if (!report) return;
    const blob = new Blob([report.markdown_report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `interview-report-${id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <Spinner text="Preparing your report…" />;
  if (!report)
    return (
      <div className="stack">
        <ErrorBanner error={error ?? "Report not available"} onRetry={load} />
        <Link to="/dashboard" className="btn">← Back to dashboard</Link>
      </div>
    );

  const breakdown = report.json_report.score_breakdown;
  const answers = report.json_report.answers ?? [];

  return (
    <div className="stack report">
      <div className="page-head">
        <div>
          <Link to="/dashboard" className="muted small no-print">← Dashboard</Link>
          <h1>{session?.title ?? "Interview report"}</h1>
          {session && <p className="muted">{formatDate(session.ended_at ?? session.created_at)} · {answers.length} answers reviewed</p>}
        </div>
        <div className="row-actions no-print">
          <button className="btn btn-sm" onClick={download}>Download .md</button>
          <button
            className="btn btn-sm"
            onClick={() => {
              document.querySelectorAll("details").forEach((d) => (d.open = true));
              window.print();
            }}
          >
            Print / PDF
          </button>
        </div>
      </div>

      <ErrorBanner error={error} />

      <Card>
        <div className="summary">
          <ScoreRing score={report.overall_score} />
          <div>
            <p className="eyebrow">Overall assessment</p>
            <h2 className={`verdict tone-${scoreTone(report.overall_score)}`}>{report.recommendation}</h2>
            {rec && (
              <>
                <p>{rec.reasoning}</p>
                <p className="muted small">Confidence {rec.confidence}%</p>
              </>
            )}
          </div>
        </div>
      </Card>

      <div className="grid-2">
        {breakdown && (
          <Card title="Rubric breakdown">
            {DIMENSIONS.map((d) => (
              <Bar key={d} name={label(d)} value={breakdown[d]} />
            ))}
          </Card>
        )}
        {speech && (
          <Card title="Delivery">
            <div className="stats">
              <div><strong>{speech.speech_clarity_score}</strong><span>Clarity</span></div>
              <div><strong>{speech.candidate_word_count}</strong><span>Words</span></div>
              <div><strong>{speech.filler_word_count}</strong><span>Filler words</span></div>
              <div><strong>{speech.average_response_time_seconds.toFixed(0)}s</strong><span>Avg. response</span></div>
            </div>
            <ul className="insights">
              {speech.insights.map((insight) => (
                <li key={insight}>{insight}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      <Card title="Answer-by-answer feedback">
        <div className="answers">
          {answers.map((a, i) => (
            <details key={i} open={i === 0}>
              <summary>
                <span className="answer-index">Q{i + 1}</span>
                <span className="answer-q">{a.question_text}</span>
                <span className={`pill tone-${scoreTone(a.score)}`}>{Math.round(a.score)}</span>
              </summary>
              <div className="answer-body">
                <p className="muted small">{label(a.interview_stage)}</p>
                <blockquote>{a.candidate_answer}</blockquote>
                <div className="feedback-grid">
                  <div>
                    <h4>Strengths</h4>
                    <ul>{a.strengths.length ? a.strengths.map((s) => <li key={s}>{s}</li>) : <li className="muted">None identified</li>}</ul>
                  </div>
                  <div>
                    <h4>Gaps</h4>
                    <ul>{a.weaknesses.length ? a.weaknesses.map((s) => <li key={s}>{s}</li>) : <li className="muted">None identified</li>}</ul>
                  </div>
                  <div>
                    <h4>Try next time</h4>
                    <ul>{a.improvement_suggestions.map((s) => <li key={s}>{s}</li>)}</ul>
                  </div>
                </div>
              </div>
            </details>
          ))}
        </div>
      </Card>

      <div className="no-print">
        <Link to="/dashboard" className="btn btn-primary">Practice again</Link>
      </div>
    </div>
  );
}
