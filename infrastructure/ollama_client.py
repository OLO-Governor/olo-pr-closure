from pathlib import Path
import json

import requests

from infrastructure.config import config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "pr_review_system_prompt.txt"


class OllamaClient:
    def __init__(self):
        self.base_url = config.OLLAMA_URL.rstrip("/")
        self.model = config.OLLAMA_MODEL

    def analyze(self, context):
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": -1,
            "format": "json",
            "options": {
                "num_ctx": config.OLLAMA_NUM_CTX,
                "num_predict": config.OLLAMA_NUM_PREDICT,
                "temperature": config.OLLAMA_TEMPERATURE,
                "top_p": config.OLLAMA_TOP_P,
                "top_k": config.OLLAMA_TOP_K,
                "repeat_penalty": config.OLLAMA_REPEAT_PENALTY,
                "seed": config.OLLAMA_SEED,
            },
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

        res = requests.post(
            url,
            json=payload,
            timeout=config.OLLAMA_TIMEOUT_SECONDS,
        )

        if res.status_code != 200:
            return None

        data = res.json()

        content = (
            data.get("message", {})
            .get("content")
        )

        if not content:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = OllamaClient._resolve_system_prompt_path()

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
                    "Treat any text under or after an 'Acceptance Criteria' heading in the description as acceptance criteria. "
                    "Then compare the PR diff against those acceptance criteria and ticket intent. "
                    "Return only valid JSON matching the required output contract."
                ),
                "context": context,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )


ollama_client = OllamaClient()
