import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const detailSource = readFileSync(
  join(rootDir, "src/components/workspace-case-detail.tsx"),
  "utf-8",
);

test("case detail imports updateCaseComment helper", () => {
  assert.match(detailSource, /updateCaseComment/);
});

test("case detail tracks comment edit state", () => {
  assert.match(detailSource, /editingCommentId/);
  assert.match(detailSource, /editCommentBody/);
  assert.match(detailSource, /editCommentIsInternal/);
  assert.match(detailSource, /isCommentEditSaving/);
  assert.match(detailSource, /commentEditValidationError/);
  assert.match(detailSource, /commentEditErrorMessage/);
});

test("case detail renders comment edit controls", () => {
  assert.match(detailSource, /commentEditButton/);
  assert.match(detailSource, /commentEditSave/);
  assert.match(detailSource, /commentCancelEditButton/);
  assert.match(detailSource, /commentEditSaving/);
  assert.match(detailSource, /workspace-case-comment-edit-form/);
  assert.match(detailSource, /handleCommentEditClick/);
  assert.match(detailSource, /handleCommentEditCancel/);
  assert.match(detailSource, /handleCommentEditSubmit/);
});

test("case detail keeps comment create and delete behavior", () => {
  assert.match(detailSource, /createCaseComment/);
  assert.match(detailSource, /deleteCaseComment/);
  assert.match(detailSource, /commentDeleteButton/);
  assert.match(detailSource, /handleCommentDeleteConfirm/);
});

test("case detail reloads activities after successful comment edit", () => {
  const editHandlerStart = detailSource.indexOf("async function handleCommentEditSubmit");
  const editHandlerEnd = detailSource.indexOf(
    "function handleCommentDeleteClick",
    editHandlerStart,
  );
  const editHandlerBlock = detailSource.slice(editHandlerStart, editHandlerEnd);
  assert.match(editHandlerBlock, /updateCaseComment/);
  assert.match(editHandlerBlock, /await reloadActivities\(\)/);
});
