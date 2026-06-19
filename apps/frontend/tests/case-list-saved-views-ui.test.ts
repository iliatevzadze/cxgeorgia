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

test("case list imports saved-view API helpers", () => {
  assert.match(componentSource, /from "@\/lib\/cases\/saved-views-api"/);
  assert.match(componentSource, /listCaseListViews/);
  assert.match(componentSource, /createCaseListView/);
});

test("saved views section labels exist", () => {
  assert.match(componentSource, /savedViewsLabel/);
  assert.match(componentSource, /workspace-cases-saved-views/);
  assert.match(componentSource, /saveCurrentView/);
});

test("saved view select apply and save labels exist", () => {
  assert.match(componentSource, /selectSavedView/);
  assert.match(componentSource, /name="savedViewSelect"/);
  assert.match(componentSource, /applyView/);
  assert.match(componentSource, /viewNameLabel/);
  assert.match(componentSource, /viewDescriptionLabel/);
  assert.match(componentSource, /saveView/);
  assert.match(componentSource, /name="saveViewName"/);
});

test("saved views are loaded without blocking case list", () => {
  assert.match(componentSource, /loadSavedViews/);
  assert.match(componentSource, /void loadSavedViews/);
  assert.match(componentSource, /const loadCases = useCallback/);
  const loadSavedViewsStart = componentSource.indexOf("const loadSavedViews");
  const loadCasesStart = componentSource.indexOf("const loadCases");
  assert.ok(loadSavedViewsStart > 0);
  assert.ok(loadCasesStart > 0);
  assert.notEqual(loadSavedViewsStart, loadCasesStart);
});

test("saved views load error state exists", () => {
  assert.match(componentSource, /savedViewsLoadError/);
  assert.match(componentSource, /setSavedViewsLoadError/);
});

test("empty saved views state exists", () => {
  assert.match(componentSource, /noSavedViewsYet/);
  assert.match(componentSource, /savedViews\.length === 0/);
});

test("applying a view resets offset references", () => {
  assert.match(componentSource, /function handleApplySavedView/);
  const applyStart = componentSource.indexOf("function handleApplySavedView");
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const applyBlock = componentSource.slice(applyStart, saveStart);
  assert.match(applyBlock, /offset: 0/);
});

test("applying a view applies filters references", () => {
  const applyStart = componentSource.indexOf("function handleApplySavedView");
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const applyBlock = componentSource.slice(applyStart, saveStart);
  assert.match(applyBlock, /savedViewFiltersToState/);
  assert.match(applyBlock, /view\.filters/);
});

test("applying a view applies sort references", () => {
  const applyStart = componentSource.indexOf("function handleApplySavedView");
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const applyBlock = componentSource.slice(applyStart, saveStart);
  assert.match(applyBlock, /view\.sort_by/);
  assert.match(applyBlock, /view\.sort_order/);
  assert.match(applyBlock, /CASE_LIST_DEFAULT_SORT_BY/);
  assert.match(applyBlock, /CASE_LIST_DEFAULT_SORT_ORDER/);
});

test("applying a view applies page size references", () => {
  const applyStart = componentSource.indexOf("function handleApplySavedView");
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const applyBlock = componentSource.slice(applyStart, saveStart);
  assert.match(applyBlock, /view\.page_size/);
});

test("saving current view sends filters sort and page_size references", () => {
  assert.match(componentSource, /async function handleSaveView/);
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const canGoStart = componentSource.indexOf("const canGoPrevious");
  const saveBlock = componentSource.slice(saveStart, canGoStart);
  assert.match(saveBlock, /filterStateToSavedViewFilters\(filters\)/);
  assert.match(saveBlock, /sort_by: sortBy/);
  assert.match(saveBlock, /sort_order: sortOrder/);
  assert.match(saveBlock, /page_size: pageSize/);
  assert.doesNotMatch(saveBlock, /offset/);
});

test("save view requires a non-empty name reference", () => {
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const canGoStart = componentSource.indexOf("const canGoPrevious");
  const saveBlock = componentSource.slice(saveStart, canGoStart);
  assert.match(saveBlock, /saveViewName\.trim\(\)/);
  assert.match(saveBlock, /viewNameRequired/);
});

test("duplicate and backend save error state exists", () => {
  assert.match(componentSource, /saveViewError/);
  assert.match(componentSource, /setSaveViewError/);
  assert.match(componentSource, /saveViewFailed/);
  assert.match(componentSource, /error\.status === 422/);
});

test("saved views i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.savedViewsLabel, "Saved views");
  assert.equal(kaCases.savedViewsLabel, "შენახული ხედები");
  assert.equal(enCases.noSavedViewsYet, "No saved views yet");
  assert.equal(kaCases.noSavedViewsYet, "შენახული ხედები ჯერ არ არის");
  assert.equal(enCases.applyView, "Apply view");
  assert.equal(kaCases.applyView, "გამოყენება");
  assert.equal(enCases.saveView, "Save view");
  assert.equal(kaCases.saveView, "ხედის შენახვა");
  assert.equal(enCases.savedViewCreated, "Saved view created");
  assert.equal(kaCases.savedViewCreated, "ხედი შენახულია");
  assert.equal(enCases.saveViewFailed, "Failed to save view");
  assert.equal(kaCases.saveViewFailed, "ხედის შენახვა ვერ მოხერხდა");
});
