import assert from "node:assert/strict";
import { test } from "node:test";

import { workspacePaths } from "../src/lib/workspaces/api";

test("workspacePaths.list points to workspaces collection", () => {
  assert.equal(workspacePaths.list(), "/api/v1/workspaces");
});

test("workspacePaths.create points to workspaces collection", () => {
  assert.equal(workspacePaths.create(), "/api/v1/workspaces");
});

test("workspacePaths.detail includes workspace id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    workspacePaths.detail(workspaceId),
    `/api/v1/workspaces/${workspaceId}`,
  );
});

test("workspacePaths.memberships includes workspace id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    workspacePaths.memberships(workspaceId),
    `/api/v1/workspaces/${workspaceId}/memberships`,
  );
});
