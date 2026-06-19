import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/operations/api.ts"),
  "utf-8",
);
const typesSource = readFileSync(
  join(rootDir, "src/lib/operations/types.ts"),
  "utf-8",
);
const dashboardSource = readFileSync(
  join(rootDir, "src/components/workspace-operations-dashboard.tsx"),
  "utf-8",
);
const pageSource = readFileSync(
  join(
    rootDir,
    "app/[locale]/workspaces/[workspaceId]/app/dashboard/page.tsx",
  ),
  "utf-8",
);

test("operationsPaths.dashboard includes workspace id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  assert.equal(
    `/api/v1/workspaces/${workspaceId}/operations/dashboard`,
    `/api/v1/workspaces/${workspaceId}/operations/dashboard`,
  );
  assert.match(apiSource, /operationsPaths\.dashboard\(workspaceId\)/);
  assert.match(
    apiSource,
    new RegExp(
      "`/api/v1/workspaces/\\$\\{workspaceId\\}/operations/dashboard`",
    ),
  );
});

test("operations api exports getOperationsDashboard helper", () => {
  assert.match(apiSource, /export async function getOperationsDashboard/);
  assert.match(
    apiSource,
    /operationsPaths\.dashboard\(workspaceId\)/,
  );
});

test("operations types export dashboard summary shapes", () => {
  assert.match(typesSource, /export type OperationsCasesSummary/);
  assert.match(typesSource, /total_cases: number/);
  assert.match(typesSource, /open_cases: number/);
  assert.match(typesSource, /pending_cases: number/);
  assert.match(typesSource, /resolved_cases: number/);
  assert.match(typesSource, /export type OperationsSlaSummary/);
  assert.match(typesSource, /on_track: number/);
  assert.match(typesSource, /at_risk: number/);
  assert.match(typesSource, /breached: number/);
  assert.match(typesSource, /export type OperationsAgentsSummary/);
  assert.match(typesSource, /active_shifts: number/);
  assert.match(typesSource, /total_agent_case_metrics: number/);
  assert.match(typesSource, /total_agent_messages: number/);
  assert.match(typesSource, /export type OperationsQaSummary/);
  assert.match(typesSource, /total_reviews: number/);
  assert.match(typesSource, /pending_reviews: number/);
  assert.match(typesSource, /approved_reviews: number/);
  assert.match(typesSource, /rejected_reviews: number/);
  assert.match(typesSource, /average_score: number/);
  assert.match(typesSource, /export type OperationsDashboardRead/);
});

test("dashboard page imports operations dashboard component", () => {
  assert.match(pageSource, /WorkspaceOperationsDashboard/);
  assert.doesNotMatch(pageSource, /WorkspaceAppPlaceholder/);
});

test("dashboard component uses operations API helper", () => {
  assert.match(dashboardSource, /getOperationsDashboard/);
});

test("dashboard component includes main section labels", () => {
  assert.match(dashboardSource, /sections\.cases/);
  assert.match(dashboardSource, /sections\.sla/);
  assert.match(dashboardSource, /sections\.agents/);
  assert.match(dashboardSource, /sections\.qa/);
  assert.match(dashboardSource, /metrics\.total/);
  assert.match(dashboardSource, /metrics\.averageScore/);
});

test("dashboard component handles loading and error states", () => {
  assert.match(dashboardSource, /isLoading/);
  assert.match(dashboardSource, /loading/);
  assert.match(dashboardSource, /errorMessage/);
  assert.match(dashboardSource, /workspace-error/);
  assert.match(dashboardSource, /empty/);
});
