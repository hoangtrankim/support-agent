"use client";

import { useEffect, useRef, useState } from "react";
import { sendMessage, type Ticket } from "@/lib/api";
import { STRINGS, toolLabel, type Lang } from "@/lib/i18n";

type Message = { role: "user" | "assistant"; text: string; ticket?: Ticket; error?: boolean };

const SESSION_KEY = "support-agent-session";

function loadSession(): string | null {
  try {
    return sessionStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}

function saveSession(id: string) {
  try {
    sessionStorage.setItem(SESSION_KEY, id);
  } catch {
    // storage unavailable: the session just won't survive a reload
  }
}

export default function ChatWidget({ lang }: { lang: Lang }) {
  const t = STRINGS[lang];
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [activity, setActivity] = useState<string | null>(null);
  const session = useRef<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    session.current = loadSession();
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages, activity]);

  function patchLast(fn: (m: Message) => Message) {
    setMessages((prev) => [...prev.slice(0, -1), fn(prev[prev.length - 1])]);
  }

  async function send(text: string) {
    text = text.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setMessages((prev) => [...prev, { role: "user", text }, { role: "assistant", text: "" }]);
    try {
      await sendMessage(text, session.current, {
        onSession: (id) => {
          session.current = id;
          saveSession(id);
        },
        onToken: (chunk) => {
          setActivity(null);
          patchLast((m) => ({ ...m, text: m.text + chunk }));
        },
        onToolStart: (name) => setActivity(toolLabel(lang, name)),
        onToolEnd: () => {},
        onTicket: (ticket) => {
          patchLast((m) => ({ ...m, ticket }));
          // Let the host page know (for example to show it in a CRM panel).
          window.parent?.postMessage({ type: "support-agent:ticket", sessionId: session.current, ticket }, "*");
        },
        onError: (message) => patchLast((m) => ({ ...m, text: message || t.error, error: true })),
      });
    } catch {
      patchLast((m) => ({ ...m, text: t.error, error: true }));
    } finally {
      setActivity(null);
      setBusy(false);
    }
  }

  const last = messages[messages.length - 1];
  const waiting = busy && last?.role === "assistant" && !last.text;

  return (
    <div className="widget">
      <header>
        <div className="avatar">L</div>
        <div>
          <b>{t.title}</b>
          <span>{t.subtitle}</span>
        </div>
      </header>

      <div className="thread" aria-live="polite">
        <div className="bubble assistant">{t.greeting}</div>
        {messages.length === 0 && (
          <div className="suggestions">
            {t.suggestions.map((s) => (
              <button key={s} onClick={() => send(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) =>
          m.role === "assistant" && !m.text && !m.ticket ? null : (
            <div key={i} className={`row ${m.role}`}>
              {m.text && <div className={`bubble ${m.role} ${m.error ? "error" : ""}`}>{m.text}</div>}
              {m.ticket && (
                <div className="ticket">
                  <b>
                    🎫 {t.ticket}: {m.ticket.ticket_id}
                  </b>
                  <span>{m.ticket.subject}</span>
                </div>
              )}
            </div>
          ),
        )}
        {(waiting || activity) && <div className="activity">{activity ?? "…"}</div>}
        <div ref={bottom} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder={t.placeholder} maxLength={2000} aria-label={t.placeholder} />
        <button type="submit" disabled={busy || !input.trim()}>
          {t.send}
        </button>
      </form>
    </div>
  );
}
