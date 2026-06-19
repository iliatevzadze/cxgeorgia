import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import {
  buildCaseListSearchParams,
  CASE_LIST_DEFAULT_SORT_BY,
  CASE_LIST_DEFAULT_SORT_ORDER,
  CASE_LIST_SORT_BY_OPTIONS,
  parseCaseListSortByParam,
  parseCaseListSortOrderParam,
  parseCaseListUrlState,
} from "../src/lib/cases/list-url-state";

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

const emptyFilters = {
  status: "",
  priority: "",
  source: "",
  sla_status: "",
  customer_id: "",
  assigned_to_user_id: "",
} as const;

test("CaseListFilters supports sort_by and sort_order", () => {
  assert.match(casesTypesSource, /export type CaseListFilters = \{/);
  assert.match(casesTypesSource, /sort_by\?: CaseListSortBy/);
  assert.match(casesTypesSource, /sort_order\?: CaseListSortOrder/);
});

test("listCases sends sort_by and sort_order query params", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /params\.set\("sort_by"/);
  assert.match(listBlock, /params\.set\("sort_order"/);
});

test("URL-state helper parses valid sort_by and sort_order", () => {
  const state = parseCaseListUrlState(
    new URLSearchParams({ sort_by: "priority", sort_order: "asc" }),
  );
  assert.equal(state.sortBy, "priority");
  assert.equal(state.sortOrder, "asc");
});

test("invalid sort_by falls back to created_at", () => {
  assert.equal(parseCaseListSortByParam("title"), CASE_LIST_DEFAULT_SORT_BY);
  assert.equal(
    parseCaseListUrlState(new URLSearchParams({ sort_by: "bad" })).sortBy,
    "created_at",
  );
});

test("invalid sort_order falls back to desc", () => {
  assert.equal(parseCaseListSortOrderParam("sideways"), CASE_LIST_DEFAULT_SORT_ORDER);
  assert.equal(
    parseCaseListUrlState(new URLSearchParams({ sort_order: "bad" })).sortOrder,
    "desc",
  );
});

test("default sorting values are omitted from URL", () => {
  const params = buildCaseListSearchParams(
    emptyFilters,
    50,
    0,
    CASE_LIST_DEFAULT_SORT_BY,
    CASE_LIST_DEFAULT_SORT_ORDER,
    new URLSearchParams(),
  );
  assert.equal(params.get("sort_by"), null);
  assert.equal(params.get("sort_order"), null);
});

test("case list UI includes sorting labels", () => {
  assert.match(componentSource, /sortByLabel/);
  assert.match(componentSource, /sortOrderLabel/);
  assert.match(componentSource, /workspace-cases-sorting/);
  assert.match(componentSource, /sortCases/);
});

test("case list UI includes all sort field options", () => {
  assert.match(componentSource, /CASE_LIST_SORT_BY_OPTIONS/);
  assert.match(componentSource, /sortByOptions\./);
  for (const option of CASE_LIST_SORT_BY_OPTIONS) {
    assert.match(urlStateSource, new RegExp(`"${option}"`));
  }
});

test("case list UI includes ascending and descending options", () => {
  assert.match(componentSource, /CASE_LIST_SORT_ORDER_OPTIONS/);
  assert.match(componentSource, /sortOrderOptions\./);
  assert.match(componentSource, /name="sortOrder"/);
});

test("sort changes reset offset references", () => {
  assert.match(componentSource, /function handleSortByChange/);
  assert.match(componentSource, /function handleSortOrderChange/);
  const sortByStart = componentSource.indexOf("function handleSortByChange");
  const previousPageStart = componentSource.indexOf("function handlePreviousPage");
  const sortBlock = componentSource.slice(sortByStart, previousPageStart);
  assert.match(sortBlock, /offset: 0/);
});

test("pagination page-size and filter interactions preserve sort references", () => {
  const filterChangeStart = componentSource.indexOf("function handleFilterChange");
  const clearFiltersStart = componentSource.indexOf("function handleClearFilters");
  const pageSizeChangeStart = componentSource.indexOf("function handlePageSizeChange");
  const sortByStart = componentSource.indexOf("function handleSortByChange");
  const previousPageStart = componentSource.indexOf("function handlePreviousPage");
  const nextPageStart = componentSource.indexOf("function handleNextPage");
  const canGoPreviousStart = componentSource.indexOf("const canGoPrevious");

  const filterBlock = componentSource.slice(filterChangeStart, clearFiltersStart);
  const pageSizeBlock = componentSource.slice(pageSizeChangeStart, sortByStart);
  const previousBlock = componentSource.slice(previousPageStart, nextPageStart);
  const nextBlock = componentSource.slice(nextPageStart, canGoPreviousStart);

  assert.match(filterBlock, /sortBy/);
  assert.match(filterBlock, /sortOrder/);
  assert.match(pageSizeBlock, /sortBy/);
  assert.match(pageSizeBlock, /sortOrder/);
  assert.match(previousBlock, /sortBy/);
  assert.match(previousBlock, /sortOrder/);
  assert.match(nextBlock, /sortBy/);
  assert.match(nextBlock, /sortOrder/);
});

test("clear filters does not reset sort references", () => {
  const clearFiltersStart = componentSource.indexOf("function handleClearFilters");
  const pageSizeChangeStart = componentSource.indexOf("function handlePageSizeChange");
  const clearFiltersBlock = componentSource.slice(clearFiltersStart, pageSizeChangeStart);
  assert.match(clearFiltersBlock, /EMPTY_CASE_LIST_FILTERS/);
  assert.match(clearFiltersBlock, /sortBy/);
  assert.match(clearFiltersBlock, /sortOrder/);
  assert.doesNotMatch(clearFiltersBlock, /sortBy:/);
});

test("case list sorting i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.sortByLabel, "Sort by");
  assert.equal(kaCases.sortByLabel, "სორტირება");
  assert.equal(enCases.sortOrderLabel, "Sort order");
  assert.equal(kaCases.sortOrderLabel, "სორტირების თანმიმდევრობა");
  assert.equal(enCases.sortByOptions.created_at, "Created date");
  assert.equal(kaCases.sortByOptions.created_at, "შექმნის თარიღი");
  assert.equal(enCases.sortByOptions.updated_at, "Updated date");
  assert.equal(kaCases.sortByOptions.updated_at, "განახლების თარიღი");
  assert.equal(enCases.sortOrderOptions.desc, "Descending");
  assert.equal(kaCases.sortOrderOptions.desc, "კლებადობით");
  assert.equal(enCases.sortOrderOptions.asc, "Ascending");
  assert.equal(kaCases.sortOrderOptions.asc, "ზრდადობით");
});
