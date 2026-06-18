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
  const updateStart = typesSource.indexOf("export type UniversalCaseUpdateRequest");
  const updateEnd = typesSource.indexOf("export type UniversalCaseDeleteResponse");
  const updateBlock = typesSource.slice(updateStart, updateEnd);
  assert.match(updateBlock, /title\?: string/);
  assert.match(updateBlock, /description\?: string \| null/);
  assert.match(updateBlock, /status\?: CaseStatus/);
  assert.match(updateBlock, /priority\?: CasePriority/);
  assert.match(updateBlock, /source\?: CaseSource/);
  assert.match(updateBlock, /customer_name\?: string \| null/);
  assert.match(updateBlock, /customer_email\?: string \| null/);
  assert.match(updateBlock, /external_reference\?: string \| null/);
  assert.match(updateBlock, /assigned_to_user_id\?: string \| null/);
  assert.doesNotMatch(updateBlock, /\bid\?:/);
  assert.doesNotMatch(updateBlock, /workspace_id/);
  assert.doesNotMatch(updateBlock, /created_by_user_id/);
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

test("case types export CaseCommentRead with expected fields", () => {
  assert.match(typesSource, /export type CaseCommentRead/);
  const commentReadStart = typesSource.indexOf("export type CaseCommentRead");
  const commentReadEnd = typesSource.indexOf("export type CaseCommentCreateRequest");
  const commentReadBlock = typesSource.slice(commentReadStart, commentReadEnd);
  assert.match(commentReadBlock, /id: string/);
  assert.match(commentReadBlock, /workspace_id: string/);
  assert.match(commentReadBlock, /case_id: string/);
  assert.match(commentReadBlock, /author_user_id: string \| null/);
  assert.match(commentReadBlock, /body: string/);
  assert.match(commentReadBlock, /is_internal: boolean/);
  assert.match(commentReadBlock, /created_at: string/);
  assert.match(commentReadBlock, /updated_at: string/);
});

test("case types export CaseCommentCreateRequest", () => {
  assert.match(typesSource, /export type CaseCommentCreateRequest/);
  const commentCreateStart = typesSource.indexOf(
    "export type CaseCommentCreateRequest",
  );
  const commentCreateEnd = typesSource.indexOf(
    "export type CaseCommentDeleteResponse",
  );
  const commentCreateBlock = typesSource.slice(commentCreateStart, commentCreateEnd);
  assert.match(commentCreateBlock, /body: string/);
  assert.match(commentCreateBlock, /is_internal\?: boolean/);
});

test("case types export CaseCommentDeleteResponse", () => {
  assert.match(typesSource, /export type CaseCommentDeleteResponse/);
  const deleteBlock = typesSource.slice(
    typesSource.indexOf("export type CaseCommentDeleteResponse"),
  );
  assert.match(deleteBlock, /id: string/);
  assert.match(deleteBlock, /deleted: boolean/);
});

test("case types export CaseActivityRead with expected fields", () => {
  assert.match(typesSource, /export type CaseActivityType/);
  assert.match(typesSource, /export type CaseActivityRead/);
  const activityReadStart = typesSource.indexOf("export type CaseActivityRead");
  const activityReadBlock = typesSource.slice(activityReadStart);
  assert.match(activityReadBlock, /id: string/);
  assert.match(activityReadBlock, /workspace_id: string/);
  assert.match(activityReadBlock, /case_id: string/);
  assert.match(activityReadBlock, /actor_user_id: string \| null/);
  assert.match(activityReadBlock, /activity_type: CaseActivityType/);
  assert.match(activityReadBlock, /message: string \| null/);
  assert.match(activityReadBlock, /metadata: Record<string, unknown>/);
  assert.match(activityReadBlock, /created_at: string/);
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
