import assert from "node:assert/strict";
import { test } from "node:test";

import { casePaths } from "../src/lib/cases/api";

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
