from __future__ import annotations

from pathlib import Path


class PromptLoader:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or Path(__file__).resolve().parents[1] / "agents" / "prompts")

    def load(self, name: str) -> str:
        path = self.base_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
