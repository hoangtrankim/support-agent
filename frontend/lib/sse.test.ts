import { test } from "node:test";
import assert from "node:assert/strict";
import { SseParser } from "./sse.ts";

test("parses events split across chunks", () => {
  const p = new SseParser();
  assert.deepEqual(p.push('event: token\ndata: {"te'), []);
  const out = p.push('xt":"hi"}\n\nevent: done\ndata: {}\n\n');
  assert.deepEqual(out, [
    { event: "token", data: { text: "hi" } },
    { event: "done", data: {} },
  ]);
});

test("handles CRLF and non-JSON data", () => {
  const p = new SseParser();
  assert.deepEqual(p.push("event: x\r\ndata: plain\r\n\r\n"), [{ event: "x", data: "plain" }]);
});
