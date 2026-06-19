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
  join(rootDir, "src/components/workspace-customers.tsx"),
  "utf-8",
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("CaseListFilters includes optional customer_id", () => {
  assert.match(casesTypesSource, /export type CaseListFilters = \{/);
  assert.match(casesTypesSource, /customer_id\?: string/);
});

test("listCases supports optional customer_id query param", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /filters: CaseListFilters = \{\}/);
  assert.match(listBlock, /filters\.customer_id/);
  assert.match(listBlock, /params\.set\("customer_id"/);
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

test("customers component includes Case history labels", () => {
  assert.match(componentSource, /caseHistoryTitle/);
  assert.match(componentSource, /linkedCasesTitle/);
  assert.match(componentSource, /noLinkedCases/);
  assert.match(componentSource, /workspace-customers-case-history-panel/);
});

test("customers component uses listCases from cases API", () => {
  assert.match(componentSource, /from "@\/lib\/cases\/api"/);
  assert.match(componentSource, /listCases/);
  assert.match(componentSource, /customer_id: customerId/);
  assert.doesNotMatch(
    componentSource,
    /\/api\/v1\/workspaces\/\$\{workspaceId\}\/cases/,
  );
});

test("customers component includes loading error and empty history states", () => {
  assert.match(componentSource, /isCaseHistoryLoading/);
  assert.match(componentSource, /caseHistoryLoading/);
  assert.match(componentSource, /caseHistoryError/);
  assert.match(componentSource, /workspace-empty/);
  assert.match(componentSource, /loadCaseHistory/);
});

test("customers component includes linked case field labels", () => {
  assert.match(componentSource, /caseStatusLabel/);
  assert.match(componentSource, /casePriorityLabel/);
  assert.match(componentSource, /caseSourceLabel/);
  assert.match(componentSource, /caseCreatedAtLabel/);
  assert.match(componentSource, /slaStatusLabel/);
  assert.match(componentSource, /workspaceRoutes\.appCaseDetail/);
});

test("customer case history i18n keys are aligned in en and ka", () => {
  const enCustomers = enMessages.workspaces.app.customers;
  const kaCustomers = kaMessages.workspaces.app.customers;

  assert.equal(enCustomers.caseHistoryTitle, "Case history");
  assert.equal(kaCustomers.caseHistoryTitle, "ქეისების ისტორია");
  assert.equal(enCustomers.noLinkedCases, "No linked cases yet");
  assert.equal(kaCustomers.noLinkedCases, "დაკავშირებული ქეისები ჯერ არ არის");
  assert.equal(enCustomers.linkedCasesTitle, "Linked cases");
  assert.equal(kaCustomers.linkedCasesTitle, "დაკავშირებული ქეისები");
  assert.equal(enCustomers.caseHistoryError, "Failed to load linked cases");
  assert.equal(
    kaCustomers.caseHistoryError,
    "დაკავშირებული ქეისების ჩატვირთვა ვერ მოხერხდა",
  );
  assert.equal(enCustomers.caseStatusLabel, "Case status");
  assert.equal(kaCustomers.caseStatusLabel, "ქეისის სტატუსი");
  assert.equal(enCustomers.casePriorityLabel, "Case priority");
  assert.equal(kaCustomers.casePriorityLabel, "ქეისის პრიორიტეტი");
  assert.equal(enCustomers.caseSourceLabel, "Case source");
  assert.equal(kaCustomers.caseSourceLabel, "ქეისის წყარო");
  assert.equal(enCustomers.caseCreatedAtLabel, "Created at");
  assert.equal(kaCustomers.caseCreatedAtLabel, "შექმნის დრო");
});
