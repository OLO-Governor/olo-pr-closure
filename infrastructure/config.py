import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_API_VERSION = os.getenv("JIRA_API_VERSION") or 3
    JIRA_ACCEPTANCE_CRITERIA_FIELD = os.getenv("JIRA_ACCEPTANCE_CRITERIA_FIELD")

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET") or ""

    OPENWEBUI_URL = os.getenv("OPENWEBUI_URL")
    OPENWEBUI_MODEL = os.getenv("OPENWEBUI_MODEL")
    OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")

    PRCLOSURE_PROMPT_FILE = os.getenv("PRCLOSURE_PROMPT_FILE")


config = Config()
