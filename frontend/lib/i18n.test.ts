import { test } from "node:test";
import assert from "node:assert/strict";
import { STRINGS, toolLabel } from "./i18n.ts";

test("both languages define the same keys", () => {
  assert.deepEqual(Object.keys(STRINGS.en).sort(), Object.keys(STRINGS.vi).sort());
  assert.deepEqual(Object.keys(STRINGS.en.tools).sort(), Object.keys(STRINGS.vi.tools).sort());
});

test("toolLabel falls back for unknown tools", () => {
  assert.equal(toolLabel("vi", "get_order"), "Đang kiểm tra đơn hàng…");
  assert.equal(toolLabel("en", "nope"), "…");
});
