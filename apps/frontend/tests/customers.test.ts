import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/customers/api.ts"),
  "utf-8",
);
const typesSource = readFileSync(
  join(rootDir, "src/lib/customers/types.ts"),
  "utf-8",
);
const componentSource = readFileSync(
  join(rootDir, "src/components/workspace-customers.tsx"),
  "utf-8",
);
const pageSource = readFileSync(
  join(
    rootDir,
    "app/[locale]/workspaces/[workspaceId]/app/customers/page.tsx",
  ),
  "utf-8",
);

test("customerPaths.list includes workspace id", () => {
  assert.match(
    apiSource,
    new RegExp(
      "`/api/v1/workspaces/\\$\\{workspaceId\\}/customers`",
    ),
  );
  assert.match(apiSource, /customerPaths\.list\(workspaceId\)/);
  assert.match(
    apiSource,
    /customerPaths\.detail\(workspaceId, customerId\)/,
  );
});

test("customer api exports helper functions", () => {
  assert.match(apiSource, /export async function listCustomers/);
  assert.match(apiSource, /export async function getCustomer/);
  assert.match(apiSource, /export async function createCustomer/);
  assert.match(apiSource, /export async function updateCustomer/);
  assert.match(apiSource, /export async function deleteCustomer/);
  assert.match(apiSource, /customerPaths\.create\(workspaceId\)/);
});

test("customer types export expected shapes and statuses", () => {
  assert.match(
    typesSource,
    /export type CustomerStatus = "active" \| "archived"/,
  );
  assert.match(typesSource, /export type Customer = \{/);
  assert.match(typesSource, /display_name: string/);
  assert.match(typesSource, /export type CustomerCreateRequest = \{/);
  assert.match(typesSource, /export type CustomerUpdateRequest = \{/);
  assert.match(typesSource, /export type CustomerDeleteResponse = \{/);
  assert.match(typesSource, /export type CustomerListFilters = \{/);
});

test("customers page imports customer component", () => {
  assert.match(pageSource, /WorkspaceCustomers/);
  assert.match(pageSource, /workspaceId=\{workspaceId\}/);
});

test("customers component includes main labels", () => {
  assert.match(componentSource, /workspaces\.app\.customers/);
  assert.match(componentSource, /title/);
  assert.match(componentSource, /empty/);
  assert.match(componentSource, /displayName/);
  assert.match(componentSource, /email/);
  assert.match(componentSource, /phone/);
  assert.match(componentSource, /externalId/);
  assert.match(componentSource, /locale/);
  assert.match(componentSource, /notes/);
  assert.match(componentSource, /editTitle/);
  assert.match(componentSource, /createTitle/);
});

test("customers component handles loading error and empty states", () => {
  assert.match(componentSource, /isLoading/);
  assert.match(componentSource, /loading/);
  assert.match(componentSource, /loadError/);
  assert.match(componentSource, /workspace-error/);
  assert.match(componentSource, /workspace-empty/);
  assert.match(componentSource, /detailLoading/);
});

test("customers component includes create edit and delete actions", () => {
  assert.match(componentSource, /createCustomer/);
  assert.match(componentSource, /updateCustomer/);
  assert.match(componentSource, /deleteCustomer/);
  assert.match(componentSource, /handleCreateSubmit/);
  assert.match(componentSource, /handleEditSubmit/);
  assert.match(componentSource, /handleDelete/);
  assert.match(componentSource, /createButton/);
  assert.match(componentSource, /saveButton/);
  assert.match(componentSource, /deleteButton/);
});

test("customers component includes search and status filter labels", () => {
  assert.match(componentSource, /searchLabel/);
  assert.match(componentSource, /statusAll/);
  assert.match(componentSource, /statusActive/);
  assert.match(componentSource, /statusArchived/);
  assert.match(componentSource, /statusFilter/);
  assert.match(componentSource, /listCustomers/);
});
