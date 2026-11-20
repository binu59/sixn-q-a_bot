from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from .assistant import answer  # noqa: E402
from .security import load_users  # noqa: E402

app = FastAPI()
USERS = load_users()


class Ask(BaseModel):
    user_id: str
    question: str = Field(min_length=1, max_length=1000)


@app.get("/api/users")
def users():
    return [{"id": u["id"], "name": u["name"], "title": u["title"]} for u in USERS.values()]


@app.post("/api/ask")
def ask(body: Ask):
    user = USERS.get(body.user_id)  # scope is looked up here, never taken from the request
    if not user:
        raise HTTPException(404, "Unknown user")
    try:
        return answer(user, body.question)
    except Exception:
        raise HTTPException(502, "The assistant is unavailable right now.")


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")