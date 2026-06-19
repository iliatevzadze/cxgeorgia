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
const packageJson = JSON.parse(
  readFileSync(join(rootDir, "package.json"), "utf-8"),
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("case list imports updateCaseListView and deleteCaseListView", () => {
  assert.match(componentSource, /from "@\/lib\/cases\/saved-views-api"/);
  assert.match(componentSource, /updateCaseListView/);
  assert.match(componentSource, /deleteCaseListView/);
});

test("edit and delete labels exist", () => {
  assert.match(componentSource, /editSelectedView/);
  assert.match(componentSource, /deleteSelectedView/);
  assert.match(componentSource, /saveViewChanges/);
  assert.match(componentSource, /cancelEdit/);
  assert.match(componentSource, /confirmDelete/);
  assert.match(componentSource, /cancelDelete/);
});

test("edit button and flow reference selected saved view", () => {
  assert.match(componentSource, /function handleStartEditView/);
  const editStart = componentSource.indexOf("function handleStartEditView");
  const cancelEditStart = componentSource.indexOf("function handleCancelEditView");
  const editBlock = componentSource.slice(editStart, cancelEditStart);
  assert.match(editBlock, /selectedSavedViewId/);
  assert.match(editBlock, /savedViews\.find/);
  assert.match(editBlock, /setEditViewName\(view\.name\)/);
  assert.match(editBlock, /view\.description/);
});

test("edit form includes name and description references", () => {
  assert.match(componentSource, /name="editViewName"/);
  assert.match(componentSource, /name="editViewDescription"/);
  assert.match(componentSource, /editViewName/);
  assert.match(componentSource, /editViewDescription/);
});

test("update requires non-empty name reference", () => {
  assert.match(componentSource, /async function handleUpdateView/);
  const updateStart = componentSource.indexOf("async function handleUpdateView");
  const deleteStart = componentSource.indexOf("function handleStartDeleteView");
  const updateBlock = componentSource.slice(updateStart, deleteStart);
  assert.match(updateBlock, /editViewName\.trim\(\)/);
  assert.match(updateBlock, /viewNameRequired/);
});

test("update calls updateCaseListView and reloads saved views", () => {
  const updateStart = componentSource.indexOf("async function handleUpdateView");
  const deleteStart = componentSource.indexOf("function handleStartDeleteView");
  const updateBlock = componentSource.slice(updateStart, deleteStart);
  assert.match(updateBlock, /await updateCaseListView\(/);
  assert.match(updateBlock, /await loadSavedViews\(\)/);
  assert.match(updateBlock, /selectedSavedViewId/);
});

test("update success and error states exist", () => {
  assert.match(componentSource, /updateViewError/);
  assert.match(componentSource, /setUpdateViewError/);
  assert.match(componentSource, /updateViewSuccess/);
  assert.match(componentSource, /setUpdateViewSuccess/);
  assert.match(componentSource, /savedViewUpdated/);
  assert.match(componentSource, /updateViewFailed/);
  assert.match(componentSource, /error\.status === 422/);
});

test("delete confirmation labels exist", () => {
  assert.match(componentSource, /deleteConfirmationText/);
  assert.match(componentSource, /isDeleteConfirming/);
  assert.match(componentSource, /handleCancelDeleteView/);
});

test("delete calls deleteCaseListView and reloads saved views", () => {
  assert.match(componentSource, /async function handleConfirmDeleteView/);
  const deleteStart = componentSource.indexOf(
    "async function handleConfirmDeleteView",
  );
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const deleteBlock = componentSource.slice(deleteStart, saveStart);
  assert.match(deleteBlock, /await deleteCaseListView\(/);
  assert.match(deleteBlock, /await loadSavedViews\(\)/);
});

test("delete clears selected view", () => {
  const deleteStart = componentSource.indexOf(
    "async function handleConfirmDeleteView",
  );
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const deleteBlock = componentSource.slice(deleteStart, saveStart);
  assert.match(deleteBlock, /setSelectedSavedViewId\(""\)/);
});

test("delete success and error states exist", () => {
  assert.match(componentSource, /deleteViewError/);
  assert.match(componentSource, /setDeleteViewError/);
  assert.match(componentSource, /deleteViewSuccess/);
  assert.match(componentSource, /setDeleteViewSuccess/);
  assert.match(componentSource, /savedViewDeleted/);
  assert.match(componentSource, /deleteViewFailed/);
});

test("delete does not reset current filters sort or page state", () => {
  const deleteStart = componentSource.indexOf(
    "async function handleConfirmDeleteView",
  );
  const saveStart = componentSource.indexOf("async function handleSaveView");
  const deleteBlock = componentSource.slice(deleteStart, saveStart);
  assert.doesNotMatch(deleteBlock, /replaceListUrl/);
  assert.doesNotMatch(deleteBlock, /handleClearFilters/);
  assert.doesNotMatch(deleteBlock, /EMPTY_CASE_LIST_FILTERS/);
});

test("saved view edit delete i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.editSelectedView, "Edit selected view");
  assert.equal(kaCases.editSelectedView, "არჩეული ხედის რედაქტირება");
  assert.equal(enCases.deleteSelectedView, "Delete selected view");
  assert.equal(kaCases.deleteSelectedView, "არჩეული ხედის წაშლა");
  assert.equal(enCases.saveViewChanges, "Save view changes");
  assert.equal(kaCases.saveViewChanges, "ცვლილებების შენახვა");
  assert.equal(enCases.cancelEdit, "Cancel edit");
  assert.equal(kaCases.cancelEdit, "რედაქტირების გაუქმება");
  assert.equal(enCases.confirmDelete, "Confirm delete");
  assert.equal(kaCases.confirmDelete, "წაშლის დადასტურება");
  assert.equal(enCases.cancelDelete, "Cancel delete");
  assert.equal(kaCases.cancelDelete, "წაშლის გაუქმება");
  assert.equal(enCases.savedViewUpdated, "Saved view updated");
  assert.equal(kaCases.savedViewUpdated, "ხედი განახლდა");
  assert.equal(enCases.updateViewFailed, "Update view failed");
  assert.equal(kaCases.updateViewFailed, "ხედის განახლება ვერ მოხერხდა");
  assert.equal(enCases.savedViewDeleted, "Saved view deleted");
  assert.equal(kaCases.savedViewDeleted, "ხედი წაიშალა");
  assert.equal(enCases.deleteViewFailed, "Delete view failed");
  assert.equal(kaCases.deleteViewFailed, "ხედის წაშლა ვერ მოხერხდა");
  assert.equal(
    enCases.deleteConfirmationText,
    "Delete this saved view? This cannot be undone.",
  );
  assert.equal(
    kaCases.deleteConfirmationText,
    "წავშალოთ ეს შენახული ხედი? ეს მოქმედება შეუქცევადი არ არის.",
  );
  assert.equal(enCases.noSavedViewSelected, "No saved view selected");
  assert.equal(kaCases.noSavedViewSelected, "შენახული ხედი არ არის არჩეული");
});

test("package.json includes saved views edit delete test", () => {
  assert.match(
    packageJson.scripts["test:unit"],
    /case-list-saved-views-edit-delete\.test\.ts/,
  );
});
