import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

export type Session = { userId: string; profileId: string; name: string; email: string };

const KEY = "ai-interviewer:session";

// Storage can be blocked (private mode, third-party iframes), so every access is guarded.
function load(): Session | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

function save(session: Session | null) {
  try {
    if (session) localStorage.setItem(KEY, JSON.stringify(session));
    else localStorage.removeItem(KEY);
  } catch {
    /* in-memory only */
  }
}

type Ctx = { session: Session | null; setSession: (s: Session | null) => void };
const SessionContext = createContext<Ctx>({ session: null, setSession: () => {} });

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setState] = useState<Session | null>(load);
  const setSession = useCallback((s: Session | null) => {
    save(s);
    setState(s);
  }, []);
  return <SessionContext.Provider value={{ session, setSession }}>{children}</SessionContext.Provider>;
}

export const useSession = () => useContext(SessionContext);
