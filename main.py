from fastapi import FastAPI
from dotenv import load_dotenv
from presentation.routes import router  # after env is loaded
from presentation.middleware.github_signature import GitHubSignatureMiddleware

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(GitHubSignatureMiddleware)

app.include_router(router)
