import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/agent-workforce/api.ts"),
  "utf-8",
);
const typesSource = readFileSync(
  join(rootDir, "src/lib/agent-workforce/types.ts"),
  "utf-8",
);
const panelSource = readFileSync(
  join(rootDir, "src/components/agent-workforce-panel.tsx"),
  "utf-8",
);
const pageSource = readFileSync(
  join(
    rootDir,
    "app/[locale]/workspaces/[workspaceId]/app/dashboard/page.tsx",
  ),
  "utf-8",
);

test("agentWorkforcePaths.clockIn includes workspace id", () => {
  assert.match(
    apiSource,
    new RegExp(
      "`/api/v1/workspaces/\\$\\{workspaceId\\}/agent-workforce/clock-in`",
    ),
  );
  assert.match(apiSource, /agentWorkforcePaths\.clockIn\(workspaceId\)/);
});

test("agent workforce api exports helper functions", () => {
  assert.match(apiSource, /export async function clockInAgentShift/);
  assert.match(apiSource, /export async function clockOutAgentShift/);
  assert.match(apiSource, /export async function getMyActiveAgentShift/);
  assert.match(apiSource, /export async function listActiveAgentShifts/);
  assert.match(apiSource, /export async function listAgentCaseMetrics/);
  assert.match(apiSource, /agentWorkforcePaths\.myActiveShift\(workspaceId\)/);
  assert.match(apiSource, /agentWorkforcePaths\.activeShifts\(workspaceId\)/);
  assert.match(apiSource, /agentWorkforcePaths\.caseMetrics\(workspaceId\)/);
});

test("agent workforce types export expected shapes", () => {
  assert.match(typesSource, /export type AgentShift = \{/);
  assert.match(typesSource, /clock_in_at: string/);
  assert.match(typesSource, /is_active: boolean/);
  assert.match(typesSource, /export type AgentCaseMetric = \{/);
  assert.match(typesSource, /messages_count: number/);
  assert.match(typesSource, /export type CaseMetricsFilters = \{/);
});

test("dashboard page imports workforce component", () => {
  assert.match(pageSource, /AgentWorkforcePanel/);
  assert.match(pageSource, /WorkspaceOperationsDashboard/);
});

test("workforce panel includes main labels", () => {
  assert.match(panelSource, /workspaces\.app\.workforce/);
  assert.match(panelSource, /myShift/);
  assert.match(panelSource, /activeShift/);
  assert.match(panelSource, /noActiveShift/);
  assert.match(panelSource, /activeShifts/);
  assert.match(panelSource, /caseMetrics/);
  assert.match(panelSource, /userId/);
  assert.match(panelSource, /caseId/);
});

test("workforce panel handles loading error and empty states", () => {
  assert.match(panelSource, /isLoading/);
  assert.match(panelSource, /loading/);
  assert.match(panelSource, /errorMessage/);
  assert.match(panelSource, /workspace-error/);
  assert.match(panelSource, /noActiveShifts/);
  assert.match(panelSource, /noCaseMetrics/);
  assert.match(panelSource, /workspace-empty/);
});

test("workforce panel includes clock-in and clock-out actions", () => {
  assert.match(panelSource, /clockInAgentShift/);
  assert.match(panelSource, /clockOutAgentShift/);
  assert.match(panelSource, /handleClockIn/);
  assert.match(panelSource, /handleClockOut/);
  assert.match(panelSource, /clockIn/);
  assert.match(panelSource, /clockOut/);
});
