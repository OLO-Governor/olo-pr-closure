import requests
import base64
from infrastructure.config import config


class JiraClient:
    def __init__(self):
        pair = f"{config.JIRA_EMAIL}:{config.JIRA_API_TOKEN}"
        encoded = base64.b64encode(pair.encode()).decode()

        self.base_url = config.JIRA_BASE_URL
        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json"
        }

    def get_ticket(self, key):
        api_version = config.JIRA_API_VERSION
        url = f"{self.base_url}/rest/api/{api_version}/issue/{key}"
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            return None

        data = res.json()

        return {
            "key": data["key"],
            "summary": data["fields"]["summary"],
            "description": self._extract_text(data["fields"]["description"])
        }

    def get_comments(self, issue_key):
        url = f"{self.base_url}/rest/api/{config.JIRA_API_VERSION}/issue/{issue_key}/comment"

        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            return []

        return res.json().get("comments", [])

    def add_comment_if_new(self, issue_key, body, marker):
        comments = self.get_comments(issue_key)

        for comment in comments:
            comment_body = str(comment.get("body", ""))
            if marker in comment_body:
                return False

        full_body = f"{marker}\n{body}"

        url = f"{self.base_url}/rest/api/{config.JIRA_API_VERSION}/issue/{issue_key}/comment"

        res = requests.post(
            url,
            headers=self.headers,
            json={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": full_body
                                }
                            ]
                        }
                    ]
                }
            }
        )

        return res.status_code == 201

    def upsert_comment(self, issue_key, body, marker):
        comments = self.get_comments(issue_key)

        for comment in comments:
            comment_body = str(comment.get("body", ""))

            if marker in comment_body:
                comment_id = comment["id"]

                url = f"{self.base_url}/rest/api/{config.JIRA_API_VERSION}/issue/{issue_key}/comment/{comment_id}"

                res = requests.put(
                    url,
                    headers=self.headers,
                    json={
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": marker
                                        }
                                    ]
                                },
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": body
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                )

                return res.status_code == 200

        # create new if not found
        return self.add_comment_if_new(issue_key, body, marker)

    def upsert_structured_comment(self, issue_key, checklist, marker):
        raise NotImplementedError(
            "upsert_structured_comment is deprecated. "
            "Use upsert_comment with a preformatted body."
        )

    @staticmethod
    def _extract_text(description):
        if not description:
            return ""

        try:
            return "".join(
                block.get("text", "")
                for section in description.get("content", [])
                for block in section.get("content", [])
            )
        except (KeyError, TypeError):
            return ""


jira_client = JiraClient()
