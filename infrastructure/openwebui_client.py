from pathlib import Path

import requests
import json

from infrastructure.config import config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "pr_review_system_prompt.txt"


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
        try:
            return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"System prompt file not found: {SYSTEM_PROMPT_PATH}"
            ) from exc

    @staticmethod
    def _format_context(context) -> str:
        return json.dumps(
            {
                "instruction": "Review the provided PR against the provided ticket context. Return only JSON matching "
                               "the required output contract.",
                "context": context,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )


openwebui_client = OpenWebUIClient()
