// Typed client for the AI Mock Interviewer FastAPI backend.

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "/api/v1";

export type User = { id: string; email: string; full_name: string };

export type CandidateProfile = {
  id: string;
  user_id: string;
  full_name: string;
  headline: string | null;
  current_role: string | null;
  years_experience: number | null;
  location: string | null;
  summary: string | null;
};

export type ResumeDocument = {
  id: string;
  file_name: string;
  skills: string[];
  experience_years: number | null;
  extracted_summary: string | null;
  created_at: string;
};

export type JobDescription = {
  id: string;
  file_name: string;
  title: string;
  summary: string | null;
  required_skills: string[];
  required_experience_years: number | null;
  created_at: string;
};

export type MatchResult = {
  overall_score: number;
  matched_skills: string[];
  missing_skills: string[];
  total_required_skills: number;
};

export type InterviewState = {
  current_stage: string;
  turn_count: number;
  topics_covered: string[];
  last_question: string | null;
  interview_complete: boolean;
  context?: { job_title?: string; required_skills?: string[] };
};

export type InterviewSession = {
  id: string;
  title: string;
  status: string;
  max_turns: number;
  current_turn: number;
  interview_state: InterviewState | null;
  created_at: string;
  ended_at: string | null;
};

export type TranscriptEntry = {
  id: string;
  sequence_number: number;
  speaker: "interviewer" | "candidate" | string;
  content: string;
  created_at: string;
};

export type StartResponse = { session_id: string; question: string; turn_count: number; max_turns: number };

export type AnswerResponse = {
  session_id: string;
  question: string | null;
  status: string;
  turn_count: number;
  interview_complete: boolean;
};

export type ScoreBreakdown = {
  technical_knowledge: number;
  problem_solving: number;
  communication: number;
  role_fit: number;
  confidence: number;
  experience_relevance: number;
  overall_score: number;
};

export type AnswerEvaluation = {
  question_text: string;
  candidate_answer: string;
  interview_stage: string;
  score: number;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
  dimension_scores?: Partial<ScoreBreakdown>;
};

export type Report = {
  id: string;
  overall_score: number;
  recommendation: string;
  markdown_report: string;
  json_report: { score_breakdown?: ScoreBreakdown; answers?: AnswerEvaluation[] };
};

export type Recommendation = { recommendation: string; confidence: number; reasoning: string };

export type SpeechAnalysis = {
  candidate_word_count: number;
  response_count: number;
  filler_word_count: number;
  average_response_time_seconds: number;
  speech_clarity_score: number;
  insights: string[];
};

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const isForm = init.body instanceof FormData;
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: isForm || !init.body ? init.headers : { "Content-Type": "application/json", ...init.headers },
    });
  } catch {
    throw new ApiError("Can't reach the interview server. Check that the API is running.", 0);
  }
  const text = await response.text();
  const data = text ? safeJson(text) : null;
  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
          : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }
  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

const upload = <T>(path: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return request<T>(path, { method: "POST", body: form });
};

export const api = {
  signIn: (email: string, full_name: string) => post<User>("/users/sign-in", { email, full_name }),

  listProfiles: (userId: string) => request<CandidateProfile[]>(`/candidate-profiles?user_id=${userId}`),
  createProfile: (body: Partial<CandidateProfile> & { user_id: string; full_name: string }) =>
    post<CandidateProfile>("/candidate-profiles", body),
  getProfile: (id: string) => request<CandidateProfile>(`/candidate-profiles/${id}`),
  updateProfile: (id: string, body: Partial<CandidateProfile>) =>
    request<CandidateProfile>(`/candidate-profiles/${id}`, { method: "PUT", body: JSON.stringify(body) }),

  listResumes: (profileId: string) => request<ResumeDocument[]>(`/candidate-profiles/${profileId}/resumes`),
  uploadResume: (profileId: string, file: File) =>
    upload<ResumeDocument>(`/candidate-profiles/${profileId}/resumes`, file),
  listJobs: (profileId: string) => request<JobDescription[]>(`/candidate-profiles/${profileId}/job-descriptions`),
  uploadJob: (profileId: string, file: File) =>
    upload<JobDescription>(`/candidate-profiles/${profileId}/job-descriptions`, file),
  matchJob: (profileId: string, jobId: string) =>
    post<MatchResult>(`/candidate-profiles/${profileId}/job-descriptions/${jobId}/match`),

  listInterviews: (profileId: string) =>
    request<InterviewSession[]>(`/interview-sessions?candidate_profile_id=${profileId}`),
  getInterview: (id: string) => request<InterviewSession>(`/interview-sessions/${id}`),
  deleteInterview: (id: string) => request<unknown>(`/interview-sessions/${id}`, { method: "DELETE" }),

  startInterview: (candidate_profile_id: string, title: string, job_description_id?: string) =>
    post<StartResponse>("/interviews/start", { candidate_profile_id, title, job_description_id: job_description_id || null }),
  answer: (id: string, answer: string) => post<AnswerResponse>(`/interviews/${id}/answer`, { answer }),
  complete: (id: string) => post<unknown>(`/interviews/${id}/complete`),
  evaluate: (id: string) => post<unknown>(`/interviews/${id}/evaluate`),
  transcript: (id: string) => request<{ entries: TranscriptEntry[] }>(`/interviews/${id}/transcript`),
  report: (id: string) => request<Report>(`/interviews/${id}/report`),
  recommendation: (id: string) => request<Recommendation>(`/interviews/${id}/recommendation`),
  speech: (id: string) => request<SpeechAnalysis>(`/interviews/${id}/speech-analysis`),
};
