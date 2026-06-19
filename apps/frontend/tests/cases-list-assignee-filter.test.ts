import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const casesApiSource = readFileSync(
  join(rootDir, "src/lib/cases/api.ts"),
  "utf-8",
);
const componentSource = readFileSync(
  join(rootDir, "src/components/workspace-cases-list.tsx"),
  "utf-8",
);
const workspacesApiSource = readFileSync(
  join(rootDir, "src/lib/workspaces/api.ts"),
  "utf-8",
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("case list filter UI includes assigned user filter labels", () => {
  assert.match(componentSource, /assignedUserLabel/);
  assert.match(componentSource, /allAssignees/);
  assert.match(componentSource, /name="assigneeFilter"/);
  assert.match(componentSource, /workspace-cases-filters/);
});

test("assigned user filter reuses existing membership/workspace API", () => {
  assert.match(componentSource, /from "@\/lib\/workspaces\/api"/);
  assert.match(componentSource, /listWorkspaceMemberships/);
  assert.match(componentSource, /item\.status === "active"/);
  assert.match(workspacesApiSource, /export async function listWorkspaceMemberships/);
});

test("listCases supports assigned_to_user_id through existing API", () => {
  const listStart = casesApiSource.indexOf("export async function listCases");
  const listEnd = casesApiSource.indexOf("export async function createCase");
  const listBlock = casesApiSource.slice(listStart, listEnd);
  assert.match(listBlock, /params\.set\("assigned_to_user_id"/);
  assert.match(componentSource, /buildCaseListFilters/);
  assert.match(
    componentSource,
    /filters\.assigned_to_user_id = state\.assigned_to_user_id/,
  );
  assert.match(componentSource, /listCases/);
});

test("All assignees option exists", () => {
  assert.match(componentSource, /allAssignees/);
  assert.match(componentSource, /<option value="">\{t\("allAssignees"\)\}</);
});

test("clear filters includes assigned_to_user_id reset references", () => {
  assert.match(componentSource, /handleClearFilters/);
  assert.match(componentSource, /EMPTY_FILTERS/);
  assert.match(componentSource, /assigned_to_user_id: ""/);
});

test("assignee load failure state exists", () => {
  assert.match(componentSource, /assigneesLoadError/);
  assert.match(componentSource, /setAssigneesLoadError/);
  assert.match(componentSource, /assigneesLoadError/);
  assert.match(componentSource, /workspace-cases-filter-error/);
});

test("case list assignee filter i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;

  assert.equal(enCases.assignedUserLabel, "Assigned user");
  assert.equal(kaCases.assignedUserLabel, "მიმაგრებული მომხმარებელი");
  assert.equal(enCases.allAssignees, "All assignees");
  assert.equal(kaCases.allAssignees, "ყველა მიმაგრებული");
  assert.equal(enCases.assigneesLoadError, "Failed to load assignees");
  assert.equal(
    kaCases.assigneesLoadError,
    "მიმაგრებულების ჩატვირთვა ვერ მოხერხდა",
  );
});
