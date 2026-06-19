import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const casesApiSource = readFileSync(
  join(rootDir, "src/lib/cases/api.ts"),
  "utf-8",
);
const casesTypesSource = readFileSync(
  join(rootDir, "src/lib/cases/types.ts"),
  "utf-8",
);
const componentSource = readFileSync(
  join(rootDir, "src/components/workspace-cases-list.tsx"),
  "utf-8",
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("CaseListFilters supports status, priority, source, assigned_to_user_id, customer_id and sla_status", () => {
  assert.match(casesTypesSource, /export type CaseListFilters = \{/);
  assert.match(casesTypesSource, /status\?: CaseStatus/);
  assert.match(casesTypesSource, /priority\?: CasePriority/);
  assert.match(casesTypesSource, /source\?: CaseSource/);
  assert.match(casesTypesSource, /assigned_to_user_id\?: string/);
  assert.match(casesTypesSource, /customer_id\?: string/);
  assert.match(casesTypesSource, /sla_status\?: CaseSlaStatus/);
});

test("listCases builds query params for supported filters", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /filters: CaseListFilters = \{\}/);
  assert.match(listBlock, /params\.set\("status"/);
  assert.match(listBlock, /params\.set\("priority"/);
  assert.match(listBlock, /params\.set\("source"/);
  assert.match(listBlock, /params\.set\("assigned_to_user_id"/);
  assert.match(listBlock, /params\.set\("customer_id"/);
  assert.match(listBlock, /params\.set\("sla_status"/);
  assert.match(listBlock, /casePaths\.list\(workspaceId\)\}\?\$\{query\}/);
});

test("listCases without filters keeps existing path behavior", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /casePaths\.list\(workspaceId\)/);
  assert.match(
    listBlock,
    /const path = query[\s\S]*: casePaths\.list\(workspaceId\)/,
  );
});

test("cases list UI includes filter labels", () => {
  assert.match(componentSource, /filtersLabel/);
  assert.match(componentSource, /filterCases/);
  assert.match(componentSource, /statusLabel/);
  assert.match(componentSource, /priorityLabel/);
  assert.match(componentSource, /sourceLabel/);
  assert.match(componentSource, /slaStatusLabel/);
  assert.match(componentSource, /workspace-cases-filters/);
});

test("cases list UI includes All options", () => {
  assert.match(componentSource, /allStatuses/);
  assert.match(componentSource, /allPriorities/);
  assert.match(componentSource, /allSources/);
  assert.match(componentSource, /allSlaStatuses/);
});

test("cases list UI includes clear filters behavior references", () => {
  assert.match(componentSource, /clearFilters/);
  assert.match(componentSource, /handleClearFilters/);
  assert.match(componentSource, /EMPTY_FILTERS/);
  assert.match(componentSource, /buildCaseListFilters/);
  assert.match(componentSource, /listCases/);
});

test("case list filter i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.filtersLabel, "Filters");
  assert.equal(kaCases.filtersLabel, "ფილტრები");
  assert.equal(enCases.filterCases, "Filter cases");
  assert.equal(kaCases.filterCases, "ქეისების ფილტრაცია");
  assert.equal(enCases.allStatuses, "All statuses");
  assert.equal(kaCases.allStatuses, "ყველა სტატუსი");
  assert.equal(enCases.allPriorities, "All priorities");
  assert.equal(kaCases.allPriorities, "ყველა პრიორიტეტი");
  assert.equal(enCases.allSources, "All sources");
  assert.equal(kaCases.allSources, "ყველა წყარო");
  assert.equal(enCases.allSlaStatuses, "All SLA statuses");
  assert.equal(kaCases.allSlaStatuses, "ყველა SLA სტატუსი");
  assert.equal(enCases.clearFilters, "Clear filters");
  assert.equal(kaCases.clearFilters, "ფილტრების გასუფთავება");
  assert.equal(enCases.statusLabel, "Status");
  assert.equal(kaCases.statusLabel, "სტატუსი");
  assert.equal(enCases.priorityLabel, "Priority");
  assert.equal(kaCases.priorityLabel, "პრიორიტეტი");
  assert.equal(enCases.sourceLabel, "Source");
  assert.equal(kaCases.sourceLabel, "წყარო");
  assert.equal(enCases.slaStatusLabel, "SLA status");
  assert.equal(kaCases.slaStatusLabel, "SLA სტატუსი");
});
