from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import db as database
from app.config import Settings, get_settings
from app.main import SessionStore, app, get_client, get_db, get_sessions


def text(value):
    return SimpleNamespace(type="text", text=value)


def tool_use(name, input, id="tu_1"):
    return SimpleNamespace(type="tool_use", name=name, input=input, id=id)


def reply(*blocks, stop_reason=None):
    has_tool = any(b.type == "tool_use" for b in blocks)
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason or ("tool_use" if has_tool else "end_turn"))


class FakeStream:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def gen():
            for block in self.response.content:
                if block.type == "text":
                    yield block.text

        return gen()

    async def get_final_message(self):
        return self.response


class FakeClient:
    """Plays back scripted Claude responses and records each request."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests: list[dict] = []
        outer = self

        class Messages:
            def stream(self, **kwargs):
                outer.requests.append({**kwargs, "messages": list(kwargs["messages"])})
                return FakeStream(outer.responses.pop(0))

        self.beta = SimpleNamespace(messages=Messages())


@pytest.fixture
def db():
    return database.connect(":memory:")


@pytest.fixture
def make_client(db):
    def _make(responses, **settings):
        fake = FakeClient(responses)
        store = SessionStore(max_sessions=settings.pop("max_sessions", 10))
        app.dependency_overrides[get_client] = lambda: fake
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_sessions] = lambda: store
        app.dependency_overrides[get_settings] = lambda: Settings(**settings)
        return TestClient(app), fake

    yield _make
    app.dependency_overrides.clear()
