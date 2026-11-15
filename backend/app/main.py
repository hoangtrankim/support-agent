import json
import sqlite3
import uuid
from collections import OrderedDict
from collections.abc import AsyncIterator
from functools import lru_cache

import anthropic
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import agent, db as database
from .config import Settings, get_settings

app = FastAPI(title="Support Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionStore:
    """Conversations kept in memory, oldest dropped first. Swap for Redis to run several servers."""

    def __init__(self, max_sessions: int):
        self.max_sessions = max_sessions
        self.sessions: OrderedDict[str, list] = OrderedDict()

    def get(self, session_id: str | None) -> tuple[str, list]:
        if session_id and session_id in self.sessions:
            self.sessions.move_to_end(session_id)
            return session_id, self.sessions[session_id]
        session_id = uuid.uuid4().hex
        self.sessions[session_id] = []
        while len(self.sessions) > self.max_sessions:
            self.sessions.popitem(last=False)
        return session_id, self.sessions[session_id]


@lru_cache
def get_sessions() -> SessionStore:
    return SessionStore(get_settings().max_sessions)


@lru_cache
def get_db() -> sqlite3.Connection:
    return database.connect(get_settings().database_path)


def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=get_settings().anthropic_api_key)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/sessions/{session_id}/tickets")
def session_tickets(session_id: str, db: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    """Tickets created during one chat session (used by the demo page)."""
    rows = db.execute(
        "SELECT id, order_id, category, priority, subject, summary, created_at FROM tickets WHERE session_id = ? ORDER BY id",
        (session_id,),
    )
    return [{**dict(r), "ticket_id": f"T-{r['id']:04d}"} for r in rows]


@app.post("/chat")
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    sessions: SessionStore = Depends(get_sessions),
    db: sqlite3.Connection = Depends(get_db),
    client: anthropic.AsyncAnthropic = Depends(get_client),
) -> StreamingResponse:
    """Send a customer message. Streams SSE events: session, token, tool_start, tool_end, ticket, done, error."""
    session_id, messages = sessions.get(body.session_id)

    async def events() -> AsyncIterator[str]:
        yield sse("session", {"session_id": session_id})
        if sum(1 for m in messages if isinstance(m["content"], str)) >= settings.max_turns_per_session:
            yield sse("error", {"message": "This conversation is too long. Please start a new chat."})
            return
        checkpoint = len(messages)
        messages.append({"role": "user", "content": body.message})
        try:
            async for event in agent.run_turn(
                client,
                db,
                messages,
                session_id=session_id,
                shop_name=settings.shop_name,
                model=settings.claude_model,
                effort=settings.claude_effort,
                max_tokens=settings.max_output_tokens,
                max_tool_rounds=settings.max_tool_rounds,
            ):
                yield sse(event.pop("type"), event)
            yield sse("done", {})
            return
        except agent.AgentError as exc:
            message = str(exc)
        except anthropic.AuthenticationError:
            message = "The Claude API key is missing or invalid."
        except anthropic.RateLimitError:
            message = "We're very busy right now. Please try again in a minute."
        except anthropic.APIStatusError as exc:
            message = f"Claude API error ({exc.status_code})."
        except anthropic.APIConnectionError:
            message = "Could not reach the Claude API."
        # Roll the conversation back so a failed turn cannot leave it in a broken state.
        del messages[checkpoint:]
        yield sse("error", {"message": message})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
