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

test("case detail renders tags section", () => {
  assert.match(detailSource, /workspace-case-tags-panel/);
  assert.match(detailSource, /tagsTitle/);
  assert.match(detailSource, /tagsEmpty/);
});

test("case detail lists attached tags", () => {
  assert.match(detailSource, /attachedTags/);
  assert.match(detailSource, /workspace-case-tag-chip/);
  assert.match(detailSource, /listCaseTags/);
});

test("case detail can attach available workspace tags", () => {
  assert.match(detailSource, /attachableTags/);
  assert.match(detailSource, /attachCaseTag/);
  assert.match(detailSource, /listWorkspaceCaseTags/);
  assert.match(detailSource, /handleAttachTagSubmit/);
});

test("case detail can create and attach a new tag", () => {
  assert.match(detailSource, /createWorkspaceCaseTag/);
  assert.match(detailSource, /handleCreateAndAttachTagSubmit/);
  assert.match(detailSource, /tagCreateAttachSuccess/);
});

test("case detail shows duplicate slug validation error", () => {
  const createHandlerStart = detailSource.indexOf(
    "async function handleCreateAndAttachTagSubmit",
  );
  const createHandlerEnd = detailSource.indexOf(
    "async function handleDetachTag",
    createHandlerStart,
  );
  const createHandlerBlock = detailSource.slice(createHandlerStart, createHandlerEnd);
  assert.match(createHandlerBlock, /tagDuplicateSlugError/);
  assert.match(createHandlerBlock, /error\.status === 422/);
});

test("case detail can detach tags", () => {
  assert.match(detailSource, /detachCaseTag/);
  assert.match(detailSource, /handleDetachTag/);
  assert.match(detailSource, /tagDetachButton/);
});

test("case detail handles tag API auth and not-found errors", () => {
  assert.match(detailSource, /tagsLoadError/);
  assert.match(detailSource, /tCommon\("accessDenied"\)/);
  assert.match(detailSource, /tCommon\("notFound"\)/);
});
