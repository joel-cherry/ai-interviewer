import { useEffect, useState } from "react";
import { useSpeaking } from "./speech";

const BAR_COUNT = 21;

/** Two eyes above a voice waveform. Bars move while the interviewer is speaking. */
export default function InterviewerAvatar({ listening = false, thinking = false }: { listening?: boolean; thinking?: boolean }) {
  const { speaking, pulse } = useSpeaking();
  const [heights, setHeights] = useState<number[]>(() => Array(BAR_COUNT).fill(0.12));

  // Drive the bars: jitter continuously while speaking, with an extra kick on each word boundary.
  useEffect(() => {
    if (!speaking) {
      setHeights(Array(BAR_COUNT).fill(0.12));
      return;
    }
    const tick = () =>
      setHeights(
        Array.from({ length: BAR_COUNT }, (_, i) => {
          const center = 1 - Math.abs(i - (BAR_COUNT - 1) / 2) / ((BAR_COUNT - 1) / 2); // taller in the middle
          return Math.max(0.12, Math.min(1, (0.25 + 0.75 * center) * (0.35 + Math.random() * 0.75)));
        }),
      );
    tick();
    const t = window.setInterval(tick, 110);
    return () => window.clearInterval(t);
  }, [speaking, pulse]);

  const state = speaking ? "speaking" : listening ? "listening" : thinking ? "thinking" : "idle";
  const caption = { speaking: "Speaking…", listening: "Listening…", thinking: "Thinking…", idle: "" }[state];

  return (
    <div className={`avatar avatar-${state}`} aria-hidden="true">
      <div className="avatar-eyes">
        <span className="avatar-eye">
          <span className="avatar-pupil" />
        </span>
        <span className="avatar-eye">
          <span className="avatar-pupil" />
        </span>
      </div>
      <div className="avatar-wave">
        {heights.map((h, i) => (
          <span key={i} style={{ transform: `scaleY(${h})` }} />
        ))}
      </div>
      <span className="avatar-caption muted small">{caption}</span>
    </div>
  );
}
