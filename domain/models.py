class PullRequest:
    def __init__(self, pr_id, branch, title):
        self.pr_id = pr_id
        self.branch = branch
        self.title = title


class Ticket:
    def __init__(self, key, summary, description):
        self.key = key
        self.summary = summary
        self.description = description
