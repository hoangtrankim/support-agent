from app import tools

SID = "s1"


def test_search_matches_english_and_vietnamese(db):
    en, _ = tools.execute(db, "search_help_articles", {"query": "how long does shipping take?"}, SID)
    assert en["articles"][0]["title"].startswith("Shipping")
    vi, _ = tools.execute(db, "search_help_articles", {"query": "Tôi muốn đổi trả hàng"}, SID)
    assert vi["articles"][0]["title"].startswith("Returns")
    plain, _ = tools.execute(db, "search_help_articles", {"query": "bao hanh"}, SID)
    assert plain["articles"][0]["title"].startswith("Warranty")
    none, _ = tools.execute(db, "search_help_articles", {"query": "zzzz"}, SID)
    assert none["articles"] == []


def test_get_order_requires_matching_email(db):
    ok, err = tools.execute(db, "get_order", {"order_id": "lh-1001", "email": "Linh.Tran@example.com"}, SID)
    assert not err and ok["found"] and ok["order"]["status"] == "shipped"
    assert len(ok["order"]["items"]) == 2 and ok["order"]["tracking_code"] == "GHN8842017"
    wrong_email, _ = tools.execute(db, "get_order", {"order_id": "LH-1001", "email": "other@example.com"}, SID)
    missing, _ = tools.execute(db, "get_order", {"order_id": "LH-9999", "email": "other@example.com"}, SID)
    assert wrong_email == missing == tools.NOT_FOUND


def test_cancel_only_while_processing(db):
    shipped, _ = tools.execute(db, "cancel_order", {"order_id": "LH-1001", "email": "linh.tran@example.com"}, SID)
    assert shipped["cancelled"] is False and shipped["status"] == "shipped"
    wrong, _ = tools.execute(db, "cancel_order", {"order_id": "LH-1002", "email": "x@example.com"}, SID)
    assert wrong == tools.NOT_FOUND
    done, _ = tools.execute(db, "cancel_order", {"order_id": "LH-1002", "email": "minh.nguyen@example.com"}, SID)
    assert done == {"cancelled": True, "order_id": "LH-1002"}
    assert db.execute("SELECT status FROM orders WHERE id='LH-1002'").fetchone()[0] == "cancelled"


def test_create_ticket_saves_row(db):
    args = {
        "email": "Sarah.Lee@example.com", "order_id": "LH-1003", "category": "damaged_item",
        "priority": "high", "subject": "Table arrived scratched", "summary": "Customer wants a replacement for a scratched table.",
    }
    result, err = tools.execute(db, "create_ticket", args, SID)
    assert not err and result == {"created": True, "ticket_id": "T-0001"}
    row = db.execute("SELECT * FROM tickets").fetchone()
    assert row["session_id"] == SID and row["email"] == "sarah.lee@example.com" and row["priority"] == "high"


def test_invalid_input_and_unknown_tool_are_errors(db):
    bad, err = tools.execute(db, "get_order", {"order_id": "LH-1001", "email": "not-an-email"}, SID)
    assert err and "email" in bad["error"]
    bad, err = tools.execute(db, "create_ticket", {"email": "a@b.co"}, SID)
    assert err
    bad, err = tools.execute(db, "get_order", "LH-1001", SID)
    assert err
    bad, err = tools.execute(db, "drop_tables", {}, SID)
    assert err and "Unknown tool" in bad["error"]
    assert db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 0


def test_tool_schemas_are_strict():
    for tool in tools.TOOLS:
        schema = tool["input_schema"]
        assert tool["strict"] is True and schema["additionalProperties"] is False
        assert sorted(schema["required"]) == sorted(schema["properties"])
