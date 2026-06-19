import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import {
  buildCaseListSearchParams,
  CASE_LIST_DEFAULT_PAGE_SIZE,
  CASE_LIST_QUERY_KEYS,
  parseCaseListLimitParam,
  parseCaseListOffsetParam,
  parseCaseListUrlState,
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

test("supported URL query param names are referenced", () => {
  for (const key of CASE_LIST_QUERY_KEYS) {
    assert.match(urlStateSource, new RegExp(`"${key}"`));
    assert.match(componentSource, new RegExp(key));
  }
});

test("initial state reads filters from URL search params", () => {
  assert.match(componentSource, /useSearchParams/);
  assert.match(componentSource, /parseCaseListUrlState/);
  const params = new URLSearchParams({
    status: "open",
    priority: "high",
    customer_id: "customer-1",
  });
  const state = parseCaseListUrlState(params);
  assert.equal(state.filters.status, "open");
  assert.equal(state.filters.priority, "high");
  assert.equal(state.filters.customer_id, "customer-1");
});

test("initial state reads valid limit and offset from URL search params", () => {
  const params = new URLSearchParams({ limit: "25", offset: "50" });
  const state = parseCaseListUrlState(params);
  assert.equal(state.pageSize, 25);
  assert.equal(state.offset, 50);
});

test("invalid limit falls back to 50", () => {
  assert.equal(parseCaseListLimitParam("200"), CASE_LIST_DEFAULT_PAGE_SIZE);
  assert.equal(parseCaseListLimitParam("bad"), CASE_LIST_DEFAULT_PAGE_SIZE);
  assert.equal(parseCaseListUrlState(new URLSearchParams({ limit: "7" })).pageSize, 50);
});

test("invalid offset falls back to 0", () => {
  assert.equal(parseCaseListOffsetParam("-1"), 0);
  assert.equal(parseCaseListOffsetParam("bad"), 0);
  assert.equal(parseCaseListUrlState(new URLSearchParams({ offset: "-5" })).offset, 0);
});

test("filter changes reset offset and update URL references", () => {
  assert.match(componentSource, /replaceListUrl/);
  assert.match(componentSource, /buildCaseListSearchParams/);
  assert.match(componentSource, /router\.replace/);
  assert.match(
    componentSource,
    /function handleFilterChange[\s\S]*offset: 0/,
  );
});

test("page-size changes update limit and reset offset references", () => {
  assert.match(
    componentSource,
    /function handlePageSizeChange[\s\S]*offset: 0/,
  );
  assert.match(componentSource, /pageSize: Number\(value\)/);
});

test("previous and next pagination updates offset references", () => {
  assert.match(componentSource, /function handlePreviousPage/);
  assert.match(componentSource, /function handleNextPage/);
  assert.match(componentSource, /offset - pageSize/);
  assert.match(componentSource, /offset \+ pageSize/);
});

test("clear filters removes filter params but keeps selected limit references", () => {
  assert.match(componentSource, /EMPTY_CASE_LIST_FILTERS/);
  const params = buildCaseListSearchParams(
    {
      status: "",
      priority: "",
      source: "",
      sla_status: "",
      customer_id: "",
      assigned_to_user_id: "",
    },
    25,
    0,
    new URLSearchParams({ status: "open", foo: "bar" }),
  );
  assert.equal(params.get("status"), null);
  assert.equal(params.get("limit"), "25");
  assert.equal(params.get("foo"), "bar");
});

test("unknown query params are preserved when rebuilding URL", () => {
  const params = buildCaseListSearchParams(
    {
      status: "open",
      priority: "",
      source: "",
      sla_status: "",
      customer_id: "",
      assigned_to_user_id: "",
    },
    50,
    10,
    new URLSearchParams({ foo: "bar", status: "pending" }),
  );
  assert.equal(params.get("foo"), "bar");
  assert.equal(params.get("status"), "open");
  assert.equal(params.get("offset"), "10");
});

test("case list pagination i18n keys remain aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.totalCasesLabel, "Total cases");
  assert.equal(kaCases.totalCasesLabel, "ქეისების რაოდენობა");
  assert.equal(enCases.pageSizeLabel, "Page size");
  assert.equal(kaCases.pageSizeLabel, "გვერდის ზომა");
});
