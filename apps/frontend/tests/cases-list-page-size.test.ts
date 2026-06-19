import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
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

test("case list UI includes page-size labels", () => {
  assert.match(componentSource, /pageSizeLabel/);
  assert.match(componentSource, /casesPerPageLabel/);
  assert.match(componentSource, /name="pageSize"/);
  assert.match(componentSource, /workspace-cases-pagination/);
});

test("page-size options 10, 25, 50, 100 exist", () => {
  assert.match(componentSource, /PAGE_SIZE_OPTIONS/);
  assert.match(componentSource, /10,\s*25,\s*50,\s*100/);
});

test("default page size is 50", () => {
  assert.match(componentSource, /DEFAULT_PAGE_SIZE = 50/);
  assert.match(componentSource, /useState\(DEFAULT_PAGE_SIZE\)/);
});

test("changing page size updates limit and resets offset references", () => {
  assert.match(componentSource, /handlePageSizeChange/);
  assert.match(componentSource, /limit: pageSize/);
  assert.match(componentSource, /setOffset\(0\)/);
  assert.match(componentSource, /setPageSize/);
});

test("filters keep selected limit and reset offset references", () => {
  const filterChangeStart = componentSource.indexOf("function handleFilterChange");
  const clearFiltersStart = componentSource.indexOf("function handleClearFilters");
  const pageSizeChangeStart = componentSource.indexOf("function handlePageSizeChange");
  const filterChangeBlock = componentSource.slice(filterChangeStart, clearFiltersStart);
  const clearFiltersBlock = componentSource.slice(clearFiltersStart, pageSizeChangeStart);

  assert.match(componentSource, /handleFilterChange/);
  assert.match(componentSource, /handleClearFilters/);
  assert.match(filterChangeBlock, /setOffset\(0\)/);
  assert.match(clearFiltersBlock, /setOffset\(0\)/);
  assert.doesNotMatch(filterChangeBlock, /setPageSize/);
  assert.doesNotMatch(clearFiltersBlock, /setPageSize/);
});

test("previous and next pagination references selected limit", () => {
  assert.match(componentSource, /handlePreviousPage/);
  assert.match(componentSource, /handleNextPage/);
  assert.match(componentSource, /current - pageSize/);
  assert.match(componentSource, /current \+ pageSize/);
  assert.match(componentSource, /offset \+ pageSize < listTotal/);
});

test("case list page size i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.pageSizeLabel, "Page size");
  assert.equal(kaCases.pageSizeLabel, "გვერდის ზომა");
  assert.equal(enCases.casesPerPageLabel, "Cases per page");
  assert.equal(kaCases.casesPerPageLabel, "ქეისები გვერდზე");
});
