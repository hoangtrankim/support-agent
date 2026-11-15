"""Tools the support agent can call, and the code that runs them.

Every tool validates its input and enforces the shop's business rules itself.
The model's arguments are never trusted: for example, order details are only
returned when the email matches the order.
"""

import re
import sqlite3
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

TOOLS = [
    {
        "name": "search_help_articles",
        "description": "Search the shop's help center for policies and how-to answers (shipping, returns, refunds, payment, warranty, cancelling). Use this before answering any policy question.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What the customer is asking about"}},
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_order",
        "description": "Look up one order's status, items, total and tracking. Requires the order number and the email used for the order; both must be provided by the customer.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order number, for example LH-1001"},
                "email": {"type": "string", "description": "Email address the customer gave"},
            },
            "required": ["order_id", "email"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an order. Only works while the order is still 'processing'. Call this only after the customer has clearly confirmed they want to cancel.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["order_id", "email"],
            "additionalProperties": False,
        },
    },
    {
        "name": "create_ticket",
        "description": "Create a support ticket for a human agent. Use when the issue needs a person: returns, refunds, damaged or wrong items, warranty claims, complaints, or anything you cannot resolve with the other tools.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer's email for follow-up"},
                "order_id": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Related order number, or null"},
                "category": {"type": "string", "enum": ["return_refund", "damaged_item", "shipping", "warranty", "payment", "other"]},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                "subject": {"type": "string", "description": "Short title in English"},
                "summary": {"type": "string", "description": "What happened and what the customer wants, in English, so staff need not reread the chat"},
            },
            "required": ["email", "order_id", "category", "priority", "subject", "summary"],
            "additionalProperties": False,
        },
    },
]

EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=300)


class OrderInput(BaseModel):
    order_id: str = Field(min_length=1, max_length=30)
    email: str = Field(pattern=EMAIL, max_length=200)


class TicketInput(BaseModel):
    email: str = Field(pattern=EMAIL, max_length=200)
    order_id: str | None = Field(default=None, max_length=30)
    category: Literal["return_refund", "damaged_item", "shipping", "warranty", "payment", "other"]
    priority: Literal["low", "normal", "high"]
    subject: str = Field(min_length=3, max_length=200)
    summary: str = Field(min_length=10, max_length=2000)


def fold(text: str) -> str:
    """Lowercase and strip Vietnamese accents so 'đổi trả' matches 'doi tra'."""
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def search_help_articles(db: sqlite3.Connection, args: SearchInput) -> dict:
    words = {w for w in re.findall(r"\w+", fold(args.query)) if len(w) > 1}
    scored = []
    for row in db.execute("SELECT title, body, keywords FROM articles"):
        haystack = set(re.findall(r"\w+", fold(f"{row['title']} {row['keywords']} {row['body']}")))
        score = len(words & haystack)
        if score:
            scored.append((score, {"title": row["title"], "body": row["body"]}))
    scored.sort(key=lambda item: -item[0])
    return {"articles": [article for _, article in scored[:3]]}


def _find_order(db: sqlite3.Connection, args: OrderInput) -> sqlite3.Row | None:
    """Return the order only if the email matches. Same answer for 'no such order' and
    'wrong email', so the tool cannot be used to discover which order numbers exist."""
    return db.execute(
        "SELECT * FROM orders WHERE id = ? AND lower(email) = ?",
        (args.order_id.strip().upper(), args.email.strip().lower()),
    ).fetchone()


NOT_FOUND = {"found": False, "message": "No order matches that order number and email. Ask the customer to check both."}


def get_order(db: sqlite3.Connection, args: OrderInput) -> dict:
    order = _find_order(db, args)
    if order is None:
        return NOT_FOUND
    items = db.execute("SELECT name, quantity, price_vnd FROM order_items WHERE order_id = ?", (order["id"],))
    return {
        "found": True,
        "order": {
            "id": order["id"],
            "customer_name": order["customer_name"],
            "status": order["status"],
            "placed_on": order["placed_on"],
            "total_vnd": order["total_vnd"],
            "carrier": order["carrier"],
            "tracking_code": order["tracking_code"],
            "estimated_delivery": order["estimated_delivery"],
            "items": [dict(item) for item in items],
        },
    }


def cancel_order(db: sqlite3.Connection, args: OrderInput) -> dict:
    order = _find_order(db, args)
    if order is None:
        return NOT_FOUND
    if order["status"] != "processing":
        return {
            "cancelled": False,
            "status": order["status"],
            "message": "Only orders that are still processing can be cancelled. Offer the returns process or a ticket instead.",
        }
    db.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order["id"],))
    db.commit()
    return {"cancelled": True, "order_id": order["id"]}


def create_ticket(db: sqlite3.Connection, args: TicketInput, session_id: str) -> dict:
    cursor = db.execute(
        "INSERT INTO tickets (session_id, email, order_id, category, priority, subject, summary) VALUES (?,?,?,?,?,?,?)",
        (session_id, args.email.strip().lower(), args.order_id, args.category, args.priority, args.subject, args.summary),
    )
    db.commit()
    return {"created": True, "ticket_id": f"T-{cursor.lastrowid:04d}"}


def execute(db: sqlite3.Connection, name: str, raw_input: object, session_id: str) -> tuple[dict, bool]:
    """Run one tool call. Returns (result, is_error)."""
    try:
        if name == "search_help_articles":
            return search_help_articles(db, SearchInput.model_validate(raw_input)), False
        if name == "get_order":
            return get_order(db, OrderInput.model_validate(raw_input)), False
        if name == "cancel_order":
            return cancel_order(db, OrderInput.model_validate(raw_input)), False
        if name == "create_ticket":
            return create_ticket(db, TicketInput.model_validate(raw_input), session_id), False
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return {"error": f"Invalid input: {problems}"}, True
    return {"error": f"Unknown tool: {name}"}, True
