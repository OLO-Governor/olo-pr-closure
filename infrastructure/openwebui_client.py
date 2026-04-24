import requests
from infrastructure.config import config


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
                    "content": """
You are a senior code reviewer focused on high-level correctness and risk.

DO NOT comment on:
- formatting or style
- linting issues
- trivial syntax or obvious mistakes
- anything a compiler, linter, or basic unit tests would catch

ONLY comment on:
- logical errors
- incorrect assumptions
- edge cases
- missing validation that affects behaviour
- security risks
- inconsistencies with ticket intent or requirements

If the code is acceptable at this level:
return an empty comments array.

Checklist must:
- map to acceptance criteria
- include meaningful validation steps only

Return ONLY valid JSON in this format:

{
  "comments": [
    { "file": "", "line": "", "comment": "" }
  ],
  "checklist": [
    { "item": "", "status": "pending" }
  ]
}

No prose. No explanation.
"""
                },
                {
                    "role": "user",
                    "content": str(context)
                }
            ]
        }

        self.headers = {
            "Authorization": f"Bearer {config.OPENWEBUI_API_KEY}",
            "Content-Type": "application/json"
        }

        res = requests.post(
            url,
            json=payload,
            headers=self.headers
        )

        if res.status_code != 200:
            return None

        return res.json()


openwebui_client = OpenWebUIClient()
