import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const typesSource = readFileSync(
  join(rootDir, "src/lib/cases/types.ts"),
  "utf-8",
);

test("case types export UniversalCaseRead", () => {
  assert.match(typesSource, /export type UniversalCaseRead/);
});

test("case status, priority and source unions match backend enums", () => {
  assert.match(typesSource, /export type CaseStatus/);
  assert.match(typesSource, /"open" \| "pending" \| "resolved" \| "closed"/);
  assert.match(typesSource, /export type CasePriority/);
  assert.match(typesSource, /"low" \| "normal" \| "high" \| "urgent"/);
  assert.match(typesSource, /export type CaseSource/);
  assert.match(typesSource, /"manual"/);
  assert.match(typesSource, /"import"/);
});
