import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/cases/attachment-api.ts"),
  "utf-8",
);
const typesSource = readFileSync(
  join(rootDir, "src/lib/cases/attachment-types.ts"),
  "utf-8",
);
const componentSource = readFileSync(
  join(rootDir, "src/components/case-attachments.tsx"),
  "utf-8",
);
const detailSource = readFileSync(
  join(rootDir, "src/components/workspace-case-detail.tsx"),
  "utf-8",
);

test("caseAttachmentPaths.list includes workspace id and case id", () => {
  assert.match(
    apiSource,
    new RegExp(
      "`/api/v1/workspaces/\\$\\{workspaceId\\}/cases/\\$\\{caseId\\}/attachments`",
    ),
  );
  assert.match(apiSource, /caseAttachmentPaths\.list\(workspaceId, caseId\)/);
  assert.match(
    apiSource,
    /caseAttachmentPaths\.detail\(workspaceId, caseId, attachmentId\)/,
  );
});

test("case attachment api exports helper functions", () => {
  assert.match(apiSource, /export async function listCaseAttachments/);
  assert.match(apiSource, /export async function uploadCaseAttachment/);
  assert.match(apiSource, /export async function deleteCaseAttachment/);
  assert.match(apiSource, /caseAttachmentPaths\.create\(workspaceId, caseId\)/);
});

test("case attachment types export expected shapes", () => {
  assert.match(typesSource, /export type CaseAttachment = \{/);
  assert.match(typesSource, /file_name: string/);
  assert.match(typesSource, /content_type: string \| null/);
  assert.match(typesSource, /size_bytes: number/);
  assert.match(typesSource, /created_at: string/);
  assert.match(typesSource, /export type CaseAttachmentDeleteResponse = \{/);
  assert.match(typesSource, /deleted: boolean/);
});

test("case detail imports attachment component", () => {
  assert.match(detailSource, /CaseAttachments/);
  assert.match(detailSource, /caseId=\{caseId\}/);
});

test("attachment component includes main labels", () => {
  assert.match(componentSource, /attachmentsTitle/);
  assert.match(componentSource, /attachmentsEmpty/);
  assert.match(componentSource, /attachmentFileName/);
  assert.match(componentSource, /attachmentContentType/);
  assert.match(componentSource, /attachmentFileSize/);
  assert.match(componentSource, /attachmentUploadedAt/);
  assert.match(componentSource, /attachmentChooseFile/);
  assert.match(componentSource, /attachmentSelectedFile/);
});

test("attachment component handles loading error and empty states", () => {
  assert.match(componentSource, /isLoading/);
  assert.match(componentSource, /attachmentsLoading/);
  assert.match(componentSource, /loadError/);
  assert.match(componentSource, /attachmentsLoadError/);
  assert.match(componentSource, /workspace-error/);
  assert.match(componentSource, /attachmentsEmpty/);
  assert.match(componentSource, /workspace-empty/);
});

test("attachment component includes upload and delete actions", () => {
  assert.match(componentSource, /uploadCaseAttachment/);
  assert.match(componentSource, /deleteCaseAttachment/);
  assert.match(componentSource, /handleUploadSubmit/);
  assert.match(componentSource, /handleDelete/);
  assert.match(componentSource, /attachmentUploadButton/);
  assert.match(componentSource, /attachmentDeleteButton/);
});

test("attachment upload uses FormData", () => {
  assert.match(apiSource, /new FormData\(\)/);
  assert.match(apiSource, /formData\.append\("file", file\)/);
  assert.match(componentSource, /uploadCaseAttachment/);
});
