import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { CASE_LIST_PAGE_SIZE_OPTIONS } from "../src/lib/cases/list-url-state";
import { caseListViewPaths } from "../src/lib/cases/saved-views-api";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/cases/saved-views-api.ts"),
  "utf-8",
);
const typesSource = readFileSync(
  join(rootDir, "src/lib/cases/saved-views-types.ts"),
  "utf-8",
);
const casesTypesSource = readFileSync(
  join(rootDir, "src/lib/cases/types.ts"),
  "utf-8",
);

const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
const viewId = "7c9e6679-7425-40de-944b-e07fc1f90ae7";

test("caseListViewPaths.list builds workspace-scoped URL", () => {
  assert.equal(
    caseListViewPaths.list(workspaceId),
    `/api/v1/workspaces/${workspaceId}/case-list-views`,
  );
});

test("caseListViewPaths.create builds workspace-scoped URL", () => {
  assert.equal(
    caseListViewPaths.create(workspaceId),
    `/api/v1/workspaces/${workspaceId}/case-list-views`,
  );
});

test("caseListViewPaths.detail includes workspace id and view id", () => {
  assert.equal(
    caseListViewPaths.detail(workspaceId, viewId),
    `/api/v1/workspaces/${workspaceId}/case-list-views/${viewId}`,
  );
});

test("saved-views API exports list create get update delete helpers", () => {
  assert.match(apiSource, /export async function listCaseListViews/);
  assert.match(apiSource, /export async function createCaseListView/);
  assert.match(apiSource, /export async function getCaseListView/);
  assert.match(apiSource, /export async function updateCaseListView/);
  assert.match(apiSource, /export async function deleteCaseListView/);
});

test("listCaseListViews uses GET", () => {
  const listStart = apiSource.indexOf("export async function listCaseListViews");
  const listEnd = apiSource.indexOf("export async function createCaseListView");
  const listBlock = apiSource.slice(listStart, listEnd);
  assert.match(listBlock, /caseListViewPaths\.list\(workspaceId\)/);
  assert.doesNotMatch(listBlock, /method:/);
});

test("createCaseListView uses POST", () => {
  assert.match(
    apiSource,
    /caseListViewPaths\.create\(workspaceId\)[\s\S]*method: "POST"/,
  );
});

test("getCaseListView uses GET", () => {
  assert.match(
    apiSource,
    /caseListViewPaths\.detail\(workspaceId, viewId\)/,
  );
  const getStart = apiSource.indexOf("export async function getCaseListView");
  const updateStart = apiSource.indexOf("export async function updateCaseListView");
  const getBlock = apiSource.slice(getStart, updateStart);
  assert.doesNotMatch(getBlock, /method: "PATCH"/);
  assert.doesNotMatch(getBlock, /method: "DELETE"/);
});

test("updateCaseListView uses PATCH", () => {
  assert.match(
    apiSource,
    /caseListViewPaths\.detail\(workspaceId, viewId\)[\s\S]*method: "PATCH"/,
  );
});

test("deleteCaseListView uses DELETE", () => {
  assert.match(
    apiSource,
    /caseListViewPaths\.detail\(workspaceId, viewId\)[\s\S]*method: "DELETE"/,
  );
});

test("CaseListViewRead includes expected fields", () => {
  assert.match(typesSource, /export type CaseListViewRead/);
  const readStart = typesSource.indexOf("export type CaseListViewRead");
  const readEnd = typesSource.indexOf("export type CaseListViewCreateRequest");
  const readBlock = typesSource.slice(readStart, readEnd);
  assert.match(readBlock, /id: string/);
  assert.match(readBlock, /workspace_id: string/);
  assert.match(readBlock, /created_by_user_id: string \| null/);
  assert.match(readBlock, /name: string/);
  assert.match(readBlock, /description: string \| null/);
  assert.match(readBlock, /filters: CaseListViewFilters/);
  assert.match(readBlock, /sort_by: CaseListSortBy \| null/);
  assert.match(readBlock, /sort_order: CaseListSortOrder \| null/);
  assert.match(readBlock, /page_size: CaseListViewPageSize \| null/);
  assert.match(readBlock, /is_default: boolean/);
  assert.match(readBlock, /created_at: string/);
  assert.match(readBlock, /updated_at: string/);
});

test("CaseListViewCreateRequest supports name description filters sort page_size is_default", () => {
  assert.match(typesSource, /export type CaseListViewCreateRequest/);
  const createStart = typesSource.indexOf("export type CaseListViewCreateRequest");
  const createEnd = typesSource.indexOf("export type CaseListViewUpdateRequest");
  const createBlock = typesSource.slice(createStart, createEnd);
  assert.match(createBlock, /name: string/);
  assert.match(createBlock, /description\?: string \| null/);
  assert.match(createBlock, /filters\?: CaseListViewFilters/);
  assert.match(createBlock, /sort_by\?: CaseListSortBy/);
  assert.match(createBlock, /sort_order\?: CaseListSortOrder/);
  assert.match(createBlock, /page_size\?: CaseListViewPageSize/);
  assert.match(createBlock, /is_default\?: boolean/);
});

test("CaseListViewUpdateRequest supports partial updates", () => {
  assert.match(typesSource, /export type CaseListViewUpdateRequest/);
  const updateStart = typesSource.indexOf("export type CaseListViewUpdateRequest");
  const updateEnd = typesSource.indexOf("export type CaseListViewDeleteResponse");
  const updateBlock = typesSource.slice(updateStart, updateEnd);
  assert.match(updateBlock, /name\?: string/);
  assert.match(updateBlock, /description\?: string \| null/);
  assert.match(updateBlock, /filters\?: CaseListViewFilters/);
  assert.match(updateBlock, /sort_by\?: CaseListSortBy \| null/);
  assert.match(updateBlock, /sort_order\?: CaseListSortOrder \| null/);
  assert.match(updateBlock, /page_size\?: CaseListViewPageSize \| null/);
  assert.match(updateBlock, /is_default\?: boolean/);
});

test("CaseListViewFilters supports case list filter fields", () => {
  assert.match(typesSource, /export type CaseListViewFilters/);
  const filtersStart = typesSource.indexOf("export type CaseListViewFilters");
  const filtersEnd = typesSource.indexOf("export type CaseListViewRead");
  const filtersBlock = typesSource.slice(filtersStart, filtersEnd);
  assert.match(filtersBlock, /status\?: CaseStatus/);
  assert.match(filtersBlock, /priority\?: CasePriority/);
  assert.match(filtersBlock, /source\?: CaseSource/);
  assert.match(filtersBlock, /sla_status\?: CaseSlaStatus/);
  assert.match(filtersBlock, /customer_id\?: string/);
  assert.match(filtersBlock, /assigned_to_user_id\?: string/);
});

test("sort and page-size values align with case list types", () => {
  assert.match(typesSource, /import type \{[\s\S]*CaseListSortBy/);
  assert.match(typesSource, /CaseListSortOrder/);
  assert.match(casesTypesSource, /export type CaseListSortBy/);
  assert.match(casesTypesSource, /created_at/);
  assert.match(casesTypesSource, /updated_at/);
  assert.match(casesTypesSource, /sla_status/);
  assert.match(typesSource, /export type CaseListViewPageSize = 10 \| 25 \| 50 \| 100/);
  assert.deepEqual([...CASE_LIST_PAGE_SIZE_OPTIONS], [10, 25, 50, 100]);
});

test("saved-views API does not import UI components", () => {
  assert.doesNotMatch(apiSource, /@\/components\//);
  assert.doesNotMatch(typesSource, /@\/components\//);
});
