import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

// Browser speech: SpeechRecognition (Chrome/Edge/Safari) for dictation, speechSynthesis for reading questions.

type Recognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((e: { resultIndex: number; results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: { error: string }) => void) | null;
};

const RecognitionCtor: (new () => Recognition) | undefined =
  (window as unknown as { SpeechRecognition?: new () => Recognition }).SpeechRecognition ||
  (window as unknown as { webkitSpeechRecognition?: new () => Recognition }).webkitSpeechRecognition;

export const canDictate = Boolean(RecognitionCtor);
export const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

// ---------- Voice selection ----------

// Neural/"natural" voices sound far less robotic. Edge ships Microsoft's online natural voices,
// Chrome ships Google's network voices, macOS/iOS ship Samantha & co.
const PREFERRED_VOICES = [
  /Microsoft (Aria|Jenny|Ava|Emma|Andrew|Brian|Guy).*Natural/i,
  /Natural/i,
  /Google UK English Female/i,
  /Google US English/i,
  /Samantha|Ava|Allison|Serena|Karen|Daniel/i,
  /Microsoft (Zira|David|Hazel|Susan)/i,
];

let chosenVoice: SpeechSynthesisVoice | null = null;

function pickVoice(): SpeechSynthesisVoice | null {
  if (!canSpeak) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;
  const lang = (navigator.language || "en-US").slice(0, 2).toLowerCase();
  const sameLang = voices.filter((v) => v.lang.toLowerCase().startsWith(lang));
  const pool = sameLang.length ? sameLang : voices;
  for (const pattern of PREFERRED_VOICES) {
    const match = pool.find((v) => pattern.test(v.name));
    if (match) return match;
  }
  return pool.find((v) => v.default) ?? pool[0];
}

if (canSpeak) {
  chosenVoice = pickVoice();
  window.speechSynthesis.addEventListener?.("voiceschanged", () => {
    chosenVoice = pickVoice();
  });
}

// ---------- Speaking state (shared so the avatar can animate) ----------

type SpeakState = { speaking: boolean; pulse: number };
let speakState: SpeakState = { speaking: false, pulse: 0 };
const listeners = new Set<() => void>();

function setSpeakState(next: Partial<SpeakState>) {
  speakState = { ...speakState, ...next };
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** { speaking, pulse } — pulse increments on every spoken word boundary. */
export function useSpeaking() {
  return useSyncExternalStore(subscribe, () => speakState);
}

export function speak(text: string) {
  if (!canSpeak) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  if (!chosenVoice) chosenVoice = pickVoice();
  if (chosenVoice) {
    utterance.voice = chosenVoice;
    utterance.lang = chosenVoice.lang;
  }
  utterance.rate = 0.98;
  utterance.pitch = 1;
  utterance.onstart = () => setSpeakState({ speaking: true });
  utterance.onboundary = () => setSpeakState({ pulse: speakState.pulse + 1 });
  utterance.onend = () => setSpeakState({ speaking: false });
  utterance.onerror = () => setSpeakState({ speaking: false });
  window.speechSynthesis.speak(utterance);
}

export function stopSpeaking() {
  if (!canSpeak) return;
  window.speechSynthesis.cancel();
  setSpeakState({ speaking: false });
}

// ---------- Dictation ----------

/** Dictation hook: calls onFinal with each finalized phrase; exposes interim text while speaking. */
export function useDictation(onFinal: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<Recognition | null>(null);
  const wantRef = useRef(false); // true while the user wants the mic on
  const onFinalRef = useRef(onFinal);
  onFinalRef.current = onFinal;

  const stop = useCallback(() => {
    wantRef.current = false;
    recRef.current?.stop();
  }, []);

  const begin = useCallback(() => {
    if (!RecognitionCtor) return;
    const rec = new RecognitionCtor();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = navigator.language || "en-US";
    rec.onresult = (event) => {
      let pending = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) onFinalRef.current(result[0].transcript.trim());
        else pending += result[0].transcript;
      }
      setInterim(pending);
    };
    rec.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        wantRef.current = false;
        setError("Microphone permission was denied.");
      } else if (e.error === "network") {
        wantRef.current = false;
        setError("Voice input couldn't reach the speech service. Check your connection, or open the app in Chrome or Edge.");
      } else if (e.error !== "no-speech" && e.error !== "aborted") {
        setError(`Voice input error: ${e.error}`);
      }
    };
    rec.onend = () => {
      setInterim("");
      // Chrome ends a session after a pause or ~60s even in continuous mode — keep going until the user stops.
      if (wantRef.current) {
        try {
          begin();
          return;
        } catch {
          wantRef.current = false;
        }
      }
      setListening(false);
    };
    recRef.current = rec;
    rec.start();
  }, []);

  const start = useCallback(() => {
    if (!RecognitionCtor) return;
    stopSpeaking();
    setError(null);
    wantRef.current = true;
    begin();
    setListening(true);
  }, [begin]);

  useEffect(
    () => () => {
      wantRef.current = false;
      recRef.current?.stop();
    },
    [],
  );

  return { listening, interim, error, start, stop };
}
