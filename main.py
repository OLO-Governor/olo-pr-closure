from fastapi import FastAPI
from dotenv import load_dotenv
from presentation.routes import router  # after env is loaded

# Load environment variables
load_dotenv()

app = FastAPI()

app.include_router(router)
