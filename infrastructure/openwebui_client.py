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
                You are a code reviewer.

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
