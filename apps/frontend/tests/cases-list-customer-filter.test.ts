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
const componentSource = readFileSync(
  join(rootDir, "src/components/workspace-cases-list.tsx"),
  "utf-8",
);
const customersApiSource = readFileSync(
  join(rootDir, "src/lib/customers/api.ts"),
  "utf-8",
);
const listUrlStateSource = readFileSync(
  join(rootDir, "src/lib/cases/list-url-state.ts"),
  "utf-8",
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("case list filter UI includes customer filter labels", () => {
  assert.match(componentSource, /customerLabel/);
  assert.match(componentSource, /allCustomers/);
  assert.match(componentSource, /name="customerFilter"/);
  assert.match(componentSource, /workspace-cases-filters/);
});

test("customer filter uses existing customers API", () => {
  assert.match(componentSource, /from "@\/lib\/customers\/api"/);
  assert.match(componentSource, /listCustomers/);
  assert.match(componentSource, /status: "active"/);
  assert.match(customersApiSource, /export async function listCustomers/);
});

test("listCases is called with customer_id filter support through existing API", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /params\.set\("customer_id"/);
  assert.match(componentSource, /buildCaseListFilters/);
  assert.match(componentSource, /filters\.customer_id = state\.customer_id/);
  assert.match(componentSource, /listCases/);
});

test("All customers option exists", () => {
  assert.match(componentSource, /allCustomers/);
  assert.match(componentSource, /<option value="">\{t\("allCustomers"\)\}</);
});

test("clear filters includes customer filter reset references", () => {
  assert.match(componentSource, /handleClearFilters/);
  assert.match(componentSource, /EMPTY_CASE_LIST_FILTERS/);
  assert.match(listUrlStateSource, /customer_id: ""/);
});

test("customer load failure state exists", () => {
  assert.match(componentSource, /customersLoadError/);
  assert.match(componentSource, /setCustomersLoadError/);
  assert.match(componentSource, /create\.customersLoadError/);
  assert.match(componentSource, /workspace-cases-filter-error/);
});

test("case list customer filter i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.customerLabel, "Customer");
  assert.equal(kaCases.customerLabel, "მომხმარებელი");
  assert.equal(enCases.allCustomers, "All customers");
  assert.equal(kaCases.allCustomers, "ყველა მომხმარებელი");
  assert.equal(enCases.create.customersLoadError, "Failed to load customers");
  assert.equal(
    kaCases.create.customersLoadError,
    "მომხმარებლების ჩატვირთვა ვერ მოხერხდა",
  );
});
