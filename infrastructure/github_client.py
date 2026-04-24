import requests
from infrastructure.config import config


class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.diff"
        }

    def get_pr_diff(self, owner, repo, pr_number):
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}.diff"

        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            return None

        return res.text

    def get_pr_comments(self, owner, repo, pr_number):
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"

        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            return []

        return res.json()

    def upsert_pr_comment(self, owner, repo, pr_number, body, marker):
        comments = self.get_pr_comments(owner, repo, pr_number)

        for c in comments:
            if marker in c.get("body", ""):
                comment_id = c["id"]

                url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"

                res = requests.patch(
                    url,
                    headers=self.headers,
                    json={"body": f"{marker}\n{body}"}
                )

                return res.status_code == 200

        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"

        res = requests.post(
            url,
            headers=self.headers,
            json={"body": f"{marker}\n{body}"}
        )

        return res.status_code == 201

    def upsert_structured_pr_comment(self, owner, repo, pr_number, comments, marker):
        if not comments:
            body = "No high-level issues identified."
        else:
            body = "\n".join([
                f"- {c['file']}:{c['line']} → {c['comment']}"
                for c in comments
            ])

        return self.upsert_pr_comment(
            owner,
            repo,
            pr_number,
            body,
            marker
        )


github_client = GitHubClient()
