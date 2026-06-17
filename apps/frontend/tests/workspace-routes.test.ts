import assert from "node:assert/strict";
import { test } from "node:test";

import { workspaceRoutes } from "../src/lib/workspaces/routes";

test("workspaceRoutes.app builds workspace app path", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    workspaceRoutes.app(workspaceId),
    `/workspaces/${workspaceId}/app`,
  );
});

test("workspaceRoutes.detail builds workspace detail path", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    workspaceRoutes.detail(workspaceId),
    `/workspaces/${workspaceId}`,
  );
});

test("workspaceRoutes.list points to workspaces index", () => {
  assert.equal(workspaceRoutes.list(), "/workspaces");
});
