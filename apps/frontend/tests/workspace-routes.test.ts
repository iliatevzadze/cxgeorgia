import assert from "node:assert/strict";
import { test } from "node:test";

import { workspaceRoutes } from "../src/lib/workspaces/routes";

const workspaceId = "550e8400-e29b-41d4-a716-446655440000";

test("workspaceRoutes.app builds workspace app path", () => {
  assert.equal(
    workspaceRoutes.app(workspaceId),
    `/workspaces/${workspaceId}/app`,
  );
});

test("workspaceRoutes.appHome matches app home path", () => {
  assert.equal(
    workspaceRoutes.appHome(workspaceId),
    `/workspaces/${workspaceId}/app`,
  );
});

test("workspaceRoutes.appDashboard builds dashboard path", () => {
  assert.equal(
    workspaceRoutes.appDashboard(workspaceId),
    `/workspaces/${workspaceId}/app/dashboard`,
  );
});

test("workspaceRoutes.appCases builds cases path", () => {
  assert.equal(
    workspaceRoutes.appCases(workspaceId),
    `/workspaces/${workspaceId}/app/cases`,
  );
});

test("workspaceRoutes.appCustomers builds customers path", () => {
  assert.equal(
    workspaceRoutes.appCustomers(workspaceId),
    `/workspaces/${workspaceId}/app/customers`,
  );
});

test("workspaceRoutes.appSettings builds settings path", () => {
  assert.equal(
    workspaceRoutes.appSettings(workspaceId),
    `/workspaces/${workspaceId}/app/settings`,
  );
});

test("workspaceRoutes.detail builds workspace detail path", () => {
  assert.equal(
    workspaceRoutes.detail(workspaceId),
    `/workspaces/${workspaceId}`,
  );
});

test("workspaceRoutes.list points to workspaces index", () => {
  assert.equal(workspaceRoutes.list(), "/workspaces");
});
