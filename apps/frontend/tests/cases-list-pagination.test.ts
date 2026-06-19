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
const customersSource = readFileSync(
  join(rootDir, "src/components/workspace-customers.tsx"),
  "utf-8",
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("frontend case list response type includes items, total, limit and offset", () => {
  assert.match(casesTypesSource, /export type CaseListResponse = \{/);
  assert.match(casesTypesSource, /items: UniversalCaseRead\[\]/);
  assert.match(casesTypesSource, /total: number/);
  assert.match(casesTypesSource, /limit: number/);
  assert.match(casesTypesSource, /offset: number/);
});

test("listCases reads paginated data shape", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /Promise<CaseListResponse>/);
  assert.match(listBlock, /apiRequest<CaseListResponse>/);
});

test("listCases supports limit and offset query params", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /filters\.limit/);
  assert.match(listBlock, /params\.set\("limit"/);
  assert.match(listBlock, /filters\.offset/);
  assert.match(listBlock, /params\.set\("offset"/);
});

test("case list UI renders from paginated items", () => {
  assert.match(componentSource, /page\.items/);
  assert.match(componentSource, /setCases\(page\.items\)/);
  assert.match(componentSource, /cases\.map/);
});

test("case list UI includes total cases label", () => {
  assert.match(componentSource, /totalCasesLabel/);
  assert.match(componentSource, /listTotal/);
  assert.match(componentSource, /workspace-cases-total/);
});

test("filters reset pagination offset references", () => {
  assert.match(componentSource, /replaceListUrl/);
  assert.match(componentSource, /handleFilterChange/);
  assert.match(componentSource, /handleClearFilters/);
  assert.match(componentSource, /offset: 0/);
});

test("previous and next pagination labels exist", () => {
  assert.match(componentSource, /previousPage/);
  assert.match(componentSource, /nextPage/);
  assert.match(componentSource, /pageLabel/);
  assert.match(componentSource, /workspace-cases-pagination/);
  assert.match(componentSource, /handlePreviousPage/);
  assert.match(componentSource, /handleNextPage/);
});

test("customer case history uses paginated listCases items", () => {
  assert.match(customersSource, /listCases/);
  assert.match(customersSource, /page\.items/);
  assert.doesNotMatch(customersSource, /setLinkedCases\(items\)/);
});

test("case list pagination i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.totalCasesLabel, "Total cases");
  assert.equal(kaCases.totalCasesLabel, "ქეისების რაოდენობა");
  assert.equal(enCases.previousPage, "Previous");
  assert.equal(kaCases.previousPage, "წინა");
  assert.equal(enCases.nextPage, "Next");
  assert.equal(kaCases.nextPage, "შემდეგი");
  assert.equal(enCases.pageLabel, "Page");
  assert.equal(kaCases.pageLabel, "გვერდი");
});
