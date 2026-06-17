import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const typesSource = readFileSync(
  join(rootDir, "src/lib/workspaces/types.ts"),
  "utf-8",
);

test("workspace types export core workspace shapes", () => {
  assert.match(typesSource, /export type WorkspaceRead/);
  assert.match(typesSource, /export type WorkspaceMembershipRead/);
  assert.match(typesSource, /export type WorkspaceWithMembershipRead/);
  assert.match(typesSource, /export type WorkspaceCreateRequest/);
});

test("workspace role and status unions match backend enums", () => {
  assert.match(typesSource, /"owner" \| "admin" \| "member"/);
  assert.match(typesSource, /"active" \| "removed"/);
  assert.match(typesSource, /"active" \| "disabled"/);
});
