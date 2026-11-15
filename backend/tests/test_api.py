import json

import anthropic
import httpx

from tests.conftest import reply, text, tool_use


def parse_sse(body):
    out = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def chat(client, message, session_id=None):
    return parse_sse(client.post("/chat", json={"message": message, "session_id": session_id}).text)


def test_plain_answer_streams_tokens(make_client):
    client, fake = make_client([reply(text("Hello! "), text("How can I help?"))])
    events = chat(client, "hi")
    assert [e for e, _ in events] == ["session", "token", "token", "done"]
    assert fake.requests[0]["messages"] == [{"role": "user", "content": "hi"}]
    assert "Lumi Home" in fake.requests[0]["system"]
    assert {t["name"] for t in fake.requests[0]["tools"]} == {"search_help_articles", "get_order", "cancel_order", "create_ticket"}


def test_tool_call_round_trip(make_client):
    client, fake = make_client([
        reply(text("Let me check. "), tool_use("get_order", {"order_id": "LH-1001", "email": "linh.tran@example.com"})),
        reply(text("Your order has shipped.")),
    ])
    events = chat(client, "Where is LH-1001? linh.tran@example.com")
    assert [e for e, _ in events] == ["session", "token", "tool_start", "tool_end", "token", "done"]
    assert events[3][1] == {"name": "get_order", "ok": True}
    second = fake.requests[1]["messages"]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    result = second[2]["content"][0]
    assert result["type"] == "tool_result" and result["tool_use_id"] == "tu_1" and result["is_error"] is False
    assert json.loads(result["content"])["order"]["tracking_code"] == "GHN8842017"


def test_parallel_tool_results_go_back_in_one_message(make_client):
    client, fake = make_client([
        reply(
            tool_use("search_help_articles", {"query": "returns"}, id="a"),
            tool_use("get_order", {"order_id": "LH-1003", "email": "sarah.lee@example.com"}, id="b"),
        ),
        reply(text("Done.")),
    ])
    chat(client, "return LH-1003")
    results = fake.requests[1]["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["a", "b"]


def test_ticket_event_and_session_tickets(make_client):
    args = {
        "email": "sarah.lee@example.com", "order_id": "LH-1003", "category": "damaged_item",
        "priority": "high", "subject": "Scratched table", "summary": "Customer wants a replacement table.",
    }
    client, _ = make_client([reply(tool_use("create_ticket", args)), reply(text("Ticket T-0001 created."))])
    events = chat(client, "my table is scratched")
    ticket = next(d for e, d in events if e == "ticket")
    assert ticket == {"ticket_id": "T-0001", "subject": "Scratched table", "category": "damaged_item", "priority": "high"}
    session_id = events[0][1]["session_id"]
    listed = client.get(f"/sessions/{session_id}/tickets").json()
    assert len(listed) == 1 and listed[0]["ticket_id"] == "T-0001"
    assert client.get("/sessions/other/tickets").json() == []


def test_invalid_tool_input_is_reported_to_model(make_client):
    client, fake = make_client([
        reply(tool_use("get_order", {"order_id": "LH-1001", "email": "nope"})),
        reply(text("Could you share your email?")),
    ])
    events = chat(client, "order LH-1001")
    assert ("tool_end", {"name": "get_order", "ok": False}) in events
    assert fake.requests[1]["messages"][2]["content"][0]["is_error"] is True


def test_session_keeps_history(make_client):
    client, fake = make_client([reply(text("Hi!")), reply(text("Sure."))])
    session_id = chat(client, "hello")[0][1]["session_id"]
    events = chat(client, "one more thing", session_id)
    assert events[0][1]["session_id"] == session_id
    assert [m["role"] for m in fake.requests[1]["messages"]] == ["user", "assistant", "user"]


def test_tool_loop_is_capped(make_client):
    loop = [reply(tool_use("search_help_articles", {"query": "x"})) for _ in range(5)]
    client, fake = make_client(loop, max_tool_rounds=2)
    events = chat(client, "hi")
    assert events[-1][0] == "error" and len(fake.requests) == 3


def test_failed_turn_is_rolled_back(make_client):
    client, fake = make_client([reply(stop_reason="refusal"), reply(text("Hi!"))])
    first = chat(client, "bad")
    assert first[-1][0] == "error"
    chat(client, "hello", first[0][1]["session_id"])
    assert fake.requests[1]["messages"] == [{"role": "user", "content": "hello"}]


def test_api_error_becomes_error_event(make_client):
    client, fake = make_client([])

    def boom(**kwargs):
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))

    fake.beta.messages.stream = boom
    assert chat(client, "hi")[-1] == ("error", {"message": "Could not reach the Claude API."})


def test_conversation_length_limit(make_client):
    client, _ = make_client([reply(text("a")), reply(text("b"))], max_turns_per_session=1)
    session_id = chat(client, "one")[0][1]["session_id"]
    assert chat(client, "two", session_id)[-1][0] == "error"


def test_old_sessions_are_dropped(make_client):
    client, fake = make_client([reply(text("a")), reply(text("b")), reply(text("c"))], max_sessions=1)
    first = chat(client, "one")[0][1]["session_id"]
    chat(client, "two")
    again = chat(client, "three", first)
    assert again[0][1]["session_id"] != first
    assert fake.requests[2]["messages"] == [{"role": "user", "content": "three"}]
