import { SseParser } from "./sse";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export type Ticket = { ticket_id: string; subject: string; category: string; priority: string };

export type ChatHandlers = {
  onSession: (sessionId: string) => void;
  onToken: (text: string) => void;
  onToolStart: (name: string) => void;
  onToolEnd: (name: string) => void;
  onTicket: (ticket: Ticket) => void;
  onError: (message: string) => void;
};

export async function sendMessage(
  message: string,
  sessionId: string | null,
  handlers: ChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });
  if (!res.ok || !res.body) {
    handlers.onError(`Request failed (${res.status})`);
    return;
  }
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  const parser = new SseParser();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    for (const { event, data } of parser.push(value)) {
      const d = data as Record<string, string>;
      if (event === "session") handlers.onSession(d.session_id);
      else if (event === "token") handlers.onToken(d.text);
      else if (event === "tool_start") handlers.onToolStart(d.name);
      else if (event === "tool_end") handlers.onToolEnd(d.name);
      else if (event === "ticket") handlers.onTicket(data as Ticket);
      else if (event === "error") handlers.onError(d.message ?? "Something went wrong.");
    }
  }
}
