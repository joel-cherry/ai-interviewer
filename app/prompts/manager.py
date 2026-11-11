from __future__ import annotations

from pathlib import Path


class PromptManager:
    def __init__(self, prompt_dir: str | Path | None = None) -> None:
        self.prompt_dir = Path(prompt_dir or Path(__file__).resolve().parent)

    def get_question_prompt(self, *, interview_title: str, turn_number: int, max_turns: int) -> str:
        return (
            f"You are conducting a mock interview titled '{interview_title}'. "
            f"Ask exactly one clear and relevant interview question for turn {turn_number} of {max_turns}. "
            "Keep it concise, professional, and suitable for a candidate response. "
            "Do not ask multiple questions at once."
        )

    def get_follow_up_prompt(
        self,
        *,
        interview_title: str,
        turn_number: int,
        max_turns: int,
        prior_answer: str,
    ) -> str:
        return (
            f"You are continuing the mock interview titled '{interview_title}'. "
            f"The candidate already answered on turn {turn_number - 1}. "
            f"Their previous answer was: '{prior_answer}'. "
            f"Ask one relevant follow-up question for turn {turn_number} of {max_turns}. "
            "Keep it targeted, clear, and conversational. "
            "Do not ask multiple questions."
        )

    def get_summary_prompt(self, *, interview_title: str, transcript: str) -> str:
        return (
            f"Summarize the interview titled '{interview_title}' in a concise and professional way. "
            f"Use this transcript: {transcript}"
        )
