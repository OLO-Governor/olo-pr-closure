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

    def post_pr_comment_if_new(self, owner, repo, pr_number, body, marker):
        comments = self.get_pr_comments(owner, repo, pr_number)

        print("POSTING TO:", owner, repo, pr_number)

        for c in comments:
            if marker in c.get("body", ""):
                return False  # already posted

        full_body = f"{marker}\n{body}"

        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"

        res = requests.post(
            url,
            headers=self.headers,
            json={"body": full_body}
        )
        print("STATUS:", res.status_code)
        print("RESPONSE:", res.text)

        return res.status_code == 201


github_client = GitHubClient()
