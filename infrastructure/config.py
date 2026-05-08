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

    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "prclosure-review")
    OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))

    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "2048"))
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
    OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.8"))
    OLLAMA_TOP_K = int(os.getenv("OLLAMA_TOP_K", "20"))
    OLLAMA_REPEAT_PENALTY = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.05"))
    OLLAMA_SEED = int(os.getenv("OLLAMA_SEED", "42"))


config = Config()
