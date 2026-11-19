import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, type InterviewSession, type TranscriptEntry } from "../api";
import { canDictate, canSpeak, speak, stopSpeaking, useDictation } from "../speech";
import { ErrorBanner, STAGES, Spinner, errorMessage, label } from "../ui";
import InterviewerAvatar from "../Avatar";

export default function Interview() {
  const { id = "" } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState<InterviewSession | null>(null);
  const [entries, setEntries] = useState<TranscriptEntry[]>([]);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tts, setTts] = useState(canSpeak); // read-aloud starts on every interview
  const chatRef = useRef<HTMLDivElement>(null);
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const spokeFirst = useRef(false);

  const dictation = useDictation((text) => setAnswer((prev) => (prev ? `${prev.trimEnd()} ${text}` : text)));

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, t] = await Promise.all([api.getInterview(id), api.transcript(id)]);
      if (s.status === "completed") {
        navigate(`/report/${id}`, { replace: true });
        return;
      }
      setSession(s);
      setEntries(t.entries);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    load();
    return () => stopSpeaking();
  }, [load]);

  // Scroll the chat to the newest message (and the "thinking" dots) whenever something is added.
  useEffect(() => {
    const el = chatRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [entries.length, sending, loading]);

  const currentQuestion = [...entries].reverse().find((e) => e.speaker === "interviewer")?.content ?? "";
  const answeredCount = entries.filter((e) => e.speaker === "candidate").length;

  // Read the opening question aloud once the interview loads.
  useEffect(() => {
    if (spokeFirst.current || loading || !tts || !currentQuestion) return;
    spokeFirst.current = true;
    speak(currentQuestion);
  }, [loading, tts, currentQuestion]);

  // Keep the newest dictated words in view (the box is only ~5 lines tall).
  useEffect(() => {
    const el = answerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [answer, dictation.interim]);

  function toggleTts() {
    const next = !tts;
    setTts(next);
    if (next && currentQuestion) speak(currentQuestion);
    else stopSpeaking();
  }

  async function finish(hasAnswers: boolean) {
    setFinishing(true);
    stopSpeaking();
    dictation.stop();
    try {
      if (!hasAnswers) {
        await api.deleteInterview(id);
        navigate("/dashboard");
        return;
      }
      await api.complete(id).catch(() => undefined); // may already be completed by the last answer
      await api.evaluate(id);
      navigate(`/report/${id}`);
    } catch (err) {
      setError(errorMessage(err));
      setFinishing(false);
    }
  }

  async function submit(e?: FormEvent) {
    e?.preventDefault();
    const text = answer.trim();
    if (!text || sending || !session) return;
    dictation.stop();
    setSending(true);
    setError(null);
    const optimistic: TranscriptEntry = {
      id: `local-${Date.now()}`,
      sequence_number: entries.length + 1,
      speaker: "candidate",
      content: text,
      created_at: new Date().toISOString(),
    };
    setEntries((prev) => [...prev, optimistic]);
    setAnswer("");
    try {
      const res = await api.answer(id, text);
      if (res.interview_complete || !res.question) {
        await finish(true);
        return;
      }
      const question = res.question;
      setEntries((prev) => [
        ...prev,
        { id: `local-q-${Date.now()}`, sequence_number: prev.length + 1, speaker: "interviewer", content: question, created_at: new Date().toISOString() },
      ]);
      setSession((s) => (s ? { ...s, current_turn: res.turn_count } : s));
      if (tts) speak(question);
    } catch (err) {
      setEntries((prev) => prev.filter((x) => x.id !== optimistic.id));
      setAnswer(text);
      setError(errorMessage(err));
    } finally {
      setSending(false);
    }
  }

  function endEarly() {
    const msg = answeredCount
      ? "End the interview now and generate your report from the answers so far?"
      : "You haven't answered anything yet. Discard this interview?";
    if (window.confirm(msg)) finish(answeredCount > 0);
  }

  if (loading) return <Spinner text="Loading interview…" />;
  if (!session) return <ErrorBanner error={error ?? "Interview not found"} onRetry={load} />;
  if (finishing) return <Spinner text="Evaluating your answers…" />;

  const turn = Math.min(session.current_turn, session.max_turns);
  const stageIndex = Math.min(turn, STAGES.length) - 1;
  const role = session.interview_state?.context?.job_title;

  return (
    <div className="interview">
      <div className="page-head">
        <div>
          <h1>{session.title}</h1>
          <p className="muted">
            Question {turn} of {session.max_turns}
            {role ? ` · ${role}` : ""}
          </p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={endEarly}>
          End interview
        </button>
      </div>

      <ol className="stages" aria-label="Interview stages">
        {STAGES.slice(0, session.max_turns).map((stage, i) => (
          <li key={stage} className={i < stageIndex ? "done" : i === stageIndex ? "current" : ""}>
            {label(stage)}
          </li>
        ))}
      </ol>

      <InterviewerAvatar listening={dictation.listening} thinking={sending} />

      <div className="chat" aria-live="polite" ref={chatRef}>
        {entries.map((entry) => (
          <div key={entry.id} className={`bubble ${entry.speaker === "candidate" ? "me" : "them"}`}>
            <span className="bubble-who">{entry.speaker === "candidate" ? "You" : "Interviewer"}</span>
            <p>{entry.content}</p>
          </div>
        ))}
        {sending && (
          <div className="bubble them typing" aria-label="Interviewer is thinking">
            <span />
            <span />
            <span />
          </div>
        )}
      </div>

      <ErrorBanner error={error || dictation.error} />

      <form className="composer card" onSubmit={submit}>
        <textarea
          ref={answerRef}
          value={dictation.interim ? `${answer}${answer ? " " : ""}${dictation.interim}` : answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit();
          }}
          placeholder={dictation.listening ? "Listening… speak your answer" : "Type your answer. Tip: use Situation, Task, Action, Result."}
          rows={5}
          readOnly={dictation.listening}
          aria-label="Your answer"
        />
        <div className="composer-bar">
          <div className="composer-tools">
            {canDictate && (
              <button
                type="button"
                className={`btn btn-sm ${dictation.listening ? "btn-danger" : ""}`}
                onClick={dictation.listening ? dictation.stop : dictation.start}
              >
                {dictation.listening ? "■ Stop" : "🎙 Speak"}
              </button>
            )}
            {canSpeak && (
              <button type="button" className={`btn btn-sm ${tts ? "btn-active" : ""}`} onClick={toggleTts} aria-pressed={tts}>
                🔊 Read aloud {tts ? "on" : "off"}
              </button>
            )}
            <span className="muted small hide-sm">{answer.trim().split(/\s+/).filter(Boolean).length} words · Ctrl+Enter to send</span>
          </div>
          <button className="btn btn-primary" disabled={sending || !answer.trim()}>
            {sending ? "Sending…" : turn >= session.max_turns ? "Submit & finish" : "Submit answer"}
          </button>
        </div>
      </form>
    </div>
  );
}
