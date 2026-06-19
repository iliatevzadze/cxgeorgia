import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import {
  CASE_LIST_DEFAULT_PAGE_SIZE,
  CASE_LIST_PAGE_SIZE_OPTIONS,
} from "../src/lib/cases/list-url-state";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const componentSource = readFileSync(
  join(rootDir, "src/components/workspace-cases-list.tsx"),
  "utf-8",
);
const urlStateSource = readFileSync(
  join(rootDir, "src/lib/cases/list-url-state.ts"),
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
  assert.match(urlStateSource, /CASE_LIST_PAGE_SIZE_OPTIONS/);
  assert.deepEqual([...CASE_LIST_PAGE_SIZE_OPTIONS], [10, 25, 50, 100]);
});

test("default page size is 50", () => {
  assert.equal(CASE_LIST_DEFAULT_PAGE_SIZE, 50);
  assert.match(componentSource, /parseCaseListUrlState/);
});

test("changing page size updates limit and resets offset references", () => {
  assert.match(componentSource, /handlePageSizeChange/);
  assert.match(componentSource, /replaceListUrl/);
  const pageSizeChangeStart = componentSource.indexOf(
    "function handlePageSizeChange",
  );
  const previousPageStart = componentSource.indexOf("function handlePreviousPage");
  const pageSizeChangeBlock = componentSource.slice(
    pageSizeChangeStart,
    previousPageStart,
  );
  assert.match(pageSizeChangeBlock, /offset: 0/);
});

test("filters keep selected limit and reset offset references", () => {
  const filterChangeStart = componentSource.indexOf("function handleFilterChange");
  const clearFiltersStart = componentSource.indexOf("function handleClearFilters");
  const pageSizeChangeStart = componentSource.indexOf("function handlePageSizeChange");
  const filterChangeBlock = componentSource.slice(filterChangeStart, clearFiltersStart);
  const clearFiltersBlock = componentSource.slice(clearFiltersStart, pageSizeChangeStart);

  assert.match(filterChangeBlock, /offset: 0/);
  assert.match(clearFiltersBlock, /offset: 0/);
  assert.match(clearFiltersBlock, /pageSize/);
  assert.doesNotMatch(filterChangeBlock, /pageSize: Number/);
});

test("previous and next pagination references selected limit", () => {
  assert.match(componentSource, /offset - pageSize/);
  assert.match(componentSource, /offset \+ pageSize/);
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
