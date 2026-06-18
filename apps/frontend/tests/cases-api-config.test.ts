import assert from "node:assert/strict";
import { test } from "node:test";

import { casePaths } from "../src/lib/cases/api";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/cases/api.ts"),
  "utf-8",
);

test("casePaths.list includes workspace id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    casePaths.list(workspaceId),
    `/api/v1/workspaces/${workspaceId}/cases`,
  );
});

test("casePaths.create includes workspace id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    casePaths.create(workspaceId),
    `/api/v1/workspaces/${workspaceId}/cases`,
  );
});

test("casePaths.detail includes workspace id and case id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  const caseId = "7c9e6679-7425-40de-944b-e07fc1f90ae7";
  assert.equal(
    casePaths.detail(workspaceId, caseId),
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}`,
  );
});

test("cases api exports getCase helper", () => {
  assert.match(apiSource, /export async function getCase/);
});

test("cases api exports updateCase helper using PATCH", () => {
  assert.match(apiSource, /export async function updateCase/);
  assert.match(apiSource, /method: "PATCH"/);
  assert.match(apiSource, /casePaths\.detail\(workspaceId, caseId\)/);
});

test("cases api exports deleteCase helper using DELETE", () => {
  assert.match(apiSource, /export async function deleteCase/);
  assert.match(apiSource, /method: "DELETE"/);
  assert.match(
    apiSource,
    /casePaths\.detail\(workspaceId, caseId\)[\s\S]*method: "DELETE"/,
  );
});
