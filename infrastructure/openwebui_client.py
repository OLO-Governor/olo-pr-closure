from pathlib import Path

import requests
import json

from infrastructure.config import config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "pr_review_system_prompt.txt"


class OpenWebUIClient:
    def __init__(self):
        self.headers = None
        self.base_url = config.OPENWEBUI_URL

    def analyze(self, context):
        url = f"{self.base_url}/api/chat/completions"

        payload = {
            "model": config.OPENWEBUI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": self._load_system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._format_context(context),
                },
            ],
        }

        self.headers = {
            "Authorization": f"Bearer {config.OPENWEBUI_API_KEY}",
            "Content-Type": "application/json",
        }

        res = requests.post(
            url,
            json=payload,
            headers=self.headers,
        )

        if res.status_code != 200:
            return None

        return res.json()

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = OpenWebUIClient._resolve_system_prompt_path()

        try:
            return prompt_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"System prompt file not found: {prompt_path}"
            ) from exc

    @staticmethod
    def _resolve_system_prompt_path() -> Path:
        configured_path = config.PRCLOSURE_PROMPT_FILE

        if configured_path:
            path = Path(configured_path)

            if not path.is_absolute():
                return PROJECT_ROOT / path

            return path

        return DEFAULT_SYSTEM_PROMPT_PATH

    @staticmethod
    def _format_context(context) -> str:
        return json.dumps(
            {
                "instruction": (
                    "Review the provided PR against the provided ticket context. "
                    "First, extract the acceptance criteria from ticket.acceptance_criteria. "
                    "If ticket.acceptance_criteria is empty, extract the acceptance criteria from ticket.description. "
                    "Treat any text under or after an 'Acceptance Criteria' heading in the description as acceptance "
                    "criteria. "
                    "Then compare the PR diff against those acceptance criteria and ticket intent. "
                    "Return only JSON matching the required output contract."
                ),
                "context": context,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )


openwebui_client = OpenWebUIClient()
