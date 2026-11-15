"""SQLite database for the demo shop: customers' orders, help articles and support tickets."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL,          -- processing | shipped | delivered | cancelled
    placed_on TEXT NOT NULL,
    total_vnd INTEGER NOT NULL,
    carrier TEXT,
    tracking_code TEXT,
    estimated_delivery TEXT
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL REFERENCES orders(id),
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price_vnd INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    keywords TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    email TEXT NOT NULL,
    order_id TEXT,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    subject TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

ORDERS = [
    ("LH-1001", "linh.tran@example.com", "Tran Thuy Linh", "shipped", "2026-11-10", 1_290_000, "GHN", "GHN8842017", "2026-11-16"),
    ("LH-1002", "minh.nguyen@example.com", "Nguyen Quang Minh", "processing", "2026-11-14", 459_000, None, None, "2026-11-19"),
    ("LH-1003", "sarah.lee@example.com", "Sarah Lee", "delivered", "2026-10-28", 2_150_000, "Viettel Post", "VTP5530921", "2026-11-02"),
    ("LH-1004", "linh.tran@example.com", "Tran Thuy Linh", "cancelled", "2026-10-05", 320_000, None, None, None),
]

ITEMS = [
    ("LH-1001", "Bamboo desk lamp", 1, 890_000),
    ("LH-1001", "Linen cushion cover", 2, 200_000),
    ("LH-1002", "Ceramic pour-over coffee set", 1, 459_000),
    ("LH-1003", "Oak bedside table", 1, 2_150_000),
    ("LH-1004", "Scented candle, lemongrass", 2, 160_000),
]

ARTICLES = [
    (
        "Shipping times and fees / Thời gian và phí giao hàng",
        "Orders ship within 1-2 business days. Delivery takes 2-3 days in Ho Chi Minh City and Hanoi, and 3-6 days elsewhere in Vietnam. "
        "Shipping is free for orders over 500,000 VND; otherwise it costs 30,000 VND. We do not ship internationally yet.",
        "shipping delivery fee cost time how long giao hang van chuyen phi ship bao lau mien phi",
    ),
    (
        "Returns and refunds / Đổi trả và hoàn tiền",
        "You can return unused items within 14 days of delivery. Start a return by contacting support with your order number. "
        "Refunds go back to the original payment method within 5-7 business days after we receive the item. "
        "Sale items and candles cannot be returned unless they arrive damaged.",
        "return refund exchange money back doi tra hoan tien tra hang 14 ngay",
    ),
    (
        "Damaged or wrong item / Hàng lỗi hoặc giao sai",
        "If an item arrives damaged or is not what you ordered, contact support within 7 days with a photo. "
        "We send a replacement or a full refund, and we pay for return shipping.",
        "damaged broken wrong item defective hong vo loi giao sai nham hang",
    ),
    (
        "Changing or cancelling an order / Thay đổi hoặc hủy đơn",
        "Orders can be cancelled or changed free of charge while their status is 'processing'. "
        "Once an order has shipped it can no longer be cancelled; use the returns process after delivery instead.",
        "cancel change order address huy don thay doi dia chi",
    ),
    (
        "Payment methods / Phương thức thanh toán",
        "We accept cash on delivery (COD), bank transfer, MoMo, ZaloPay, and Visa or Mastercard. "
        "Card and e-wallet payments are charged when the order is placed.",
        "payment pay cod card momo zalopay bank transfer thanh toan the chuyen khoan",
    ),
    (
        "Warranty / Bảo hành",
        "Furniture and lamps have a 12-month warranty against manufacturing defects. Warranty claims go through a support ticket.",
        "warranty guarantee defect bao hanh 12 thang",
    ),
]


def connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)", ORDERS)
        conn.executemany("INSERT INTO order_items VALUES (?,?,?,?)", ITEMS)
        conn.executemany("INSERT INTO articles (title, body, keywords) VALUES (?,?,?)", ARTICLES)
    conn.commit()
    return conn
