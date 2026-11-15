"use client";

import { useEffect, useState } from "react";
import type { Ticket } from "@/lib/api";

const ORDERS = [
  { id: "LH-1001", email: "linh.tran@example.com", status: "shipped" },
  { id: "LH-1002", email: "minh.nguyen@example.com", status: "processing" },
  { id: "LH-1003", email: "sarah.lee@example.com", status: "delivered" },
];

const PROMPTS = [
  "Where is my order LH-1001? My email is linh.tran@example.com",
  "Tôi muốn hủy đơn LH-1002, email minh.nguyen@example.com",
  "My oak table from order LH-1003 arrived scratched (sarah.lee@example.com)",
  "Phí giao hàng là bao nhiêu?",
];

/** Explains the demo and shows tickets the agent creates, as a support team would see them. */
export default function DemoPanel() {
  const [tickets, setTickets] = useState<Ticket[]>([]);

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "support-agent:ticket") setTickets((prev) => [...prev, event.data.ticket as Ticket]);
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  return (
    <section className="demo">
      <div className="demo-card">
        <h2>Try the support agent</h2>
        <p>Open the chat in the bottom-right corner and ask about one of these demo orders. The agent only shares an order when the email matches.</p>
        <table>
          <thead>
            <tr>
              <th>Order</th>
              <th>Email</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {ORDERS.map((o) => (
              <tr key={o.id}>
                <td>{o.id}</td>
                <td>{o.email}</td>
                <td>{o.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3>Things to ask</h3>
        <ul>
          {PROMPTS.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </div>

      <div className="demo-card">
        <h2>Support team inbox</h2>
        {tickets.length === 0 ? (
          <p className="muted">Tickets the agent creates will appear here.</p>
        ) : (
          <ul className="inbox">
            {tickets.map((t) => (
              <li key={t.ticket_id}>
                <b>{t.ticket_id}</b> {t.subject}
                <span className={`tag ${t.priority}`}>{t.priority}</span>
                <span className="tag">{t.category.replace("_", " ")}</span>
              </li>
            ))}
          </ul>
        )}
        <h3>Add it to any website</h3>
        <pre>{`<script src="https://YOUR-HOST/embed.js"\n        data-lang="vi" async></script>`}</pre>
      </div>
    </section>
  );
}
