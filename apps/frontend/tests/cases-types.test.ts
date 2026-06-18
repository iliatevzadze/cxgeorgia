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

test("case types export UniversalCaseCreateRequest", () => {
  assert.match(typesSource, /export type UniversalCaseCreateRequest/);
  assert.match(typesSource, /title: string/);
  assert.match(typesSource, /description\?: string/);
  assert.match(typesSource, /priority\?: CasePriority/);
  assert.match(typesSource, /source\?: CaseSource/);
  assert.match(typesSource, /customer_name\?: string/);
  assert.match(typesSource, /customer_email\?: string/);
  assert.match(typesSource, /external_reference\?: string/);
});

test("case types export UniversalCaseUpdateRequest with allowed optional fields", () => {
  assert.match(typesSource, /export type UniversalCaseUpdateRequest/);
  const updateBlock = typesSource.slice(
    typesSource.indexOf("export type UniversalCaseUpdateRequest"),
  );
  assert.match(updateBlock, /title\?: string/);
  assert.match(updateBlock, /description\?: string \| null/);
  assert.match(updateBlock, /status\?: CaseStatus/);
  assert.match(updateBlock, /priority\?: CasePriority/);
  assert.match(updateBlock, /source\?: CaseSource/);
  assert.match(updateBlock, /customer_name\?: string \| null/);
  assert.match(updateBlock, /customer_email\?: string \| null/);
  assert.match(updateBlock, /external_reference\?: string \| null/);
  assert.doesNotMatch(updateBlock, /\bid\?:/);
  assert.doesNotMatch(updateBlock, /workspace_id/);
  assert.doesNotMatch(updateBlock, /created_by_user_id/);
  assert.doesNotMatch(updateBlock, /assigned_to_user_id/);
  assert.doesNotMatch(updateBlock, /created_at/);
  assert.doesNotMatch(updateBlock, /updated_at/);
});

test("case types export UniversalCaseDeleteResponse", () => {
  assert.match(typesSource, /export type UniversalCaseDeleteResponse/);
  const deleteBlock = typesSource.slice(
    typesSource.indexOf("export type UniversalCaseDeleteResponse"),
  );
  assert.match(deleteBlock, /id: string/);
  assert.match(deleteBlock, /deleted: boolean/);
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
