import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const typesSource = readFileSync(
  join(rootDir, "src/lib/cases/types.ts"),
  "utf-8",
);
const createFormSource = readFileSync(
  join(rootDir, "src/components/workspace-case-create-form.tsx"),
  "utf-8",
);
const detailSource = readFileSync(
  join(rootDir, "src/components/workspace-case-detail.tsx"),
  "utf-8",
);
const customersApiSource = readFileSync(
  join(rootDir, "src/lib/customers/api.ts"),
  "utf-8",
);

test("UniversalCaseRead includes customer_id", () => {
  const readStart = typesSource.indexOf("export type UniversalCaseRead");
  const readEnd = typesSource.indexOf("export type UniversalCaseCreateRequest");
  const readBlock = typesSource.slice(readStart, readEnd);
  assert.match(readBlock, /customer_id: string \| null/);
});

test("UniversalCaseCreateRequest allows optional customer_id", () => {
  const createStart = typesSource.indexOf("export type UniversalCaseCreateRequest");
  const createEnd = typesSource.indexOf("export type UniversalCaseUpdateRequest");
  const createBlock = typesSource.slice(createStart, createEnd);
  assert.match(createBlock, /customer_id\?: string \| null/);
});

test("UniversalCaseUpdateRequest allows optional customer_id", () => {
  const updateStart = typesSource.indexOf("export type UniversalCaseUpdateRequest");
  const updateEnd = typesSource.indexOf("export type UniversalCaseDeleteResponse");
  const updateBlock = typesSource.slice(updateStart, updateEnd);
  assert.match(updateBlock, /customer_id\?: string \| null/);
});

test("case create form includes customer selector labels", () => {
  assert.match(createFormSource, /selectCustomer/);
  assert.match(createFormSource, /noCustomer/);
  assert.match(createFormSource, /customersLoading/);
  assert.match(createFormSource, /customersLoadError/);
  assert.match(createFormSource, /customer_id/);
});

test("case create form reuses customers API", () => {
  assert.match(createFormSource, /from "@\/lib\/customers\/api"/);
  assert.match(createFormSource, /listCustomers/);
  assert.doesNotMatch(createFormSource, /\/api\/v1\/workspaces\/\$\{workspaceId\}\/customers/);
});

test("case detail imports and uses customer linking UI", () => {
  assert.match(detailSource, /from "@\/lib\/customers\/api"/);
  assert.match(detailSource, /listCustomers/);
  assert.match(detailSource, /workspace-case-customer-panel/);
  assert.match(detailSource, /handleCustomerLinkSubmit/);
  assert.match(detailSource, /customer_id/);
});

test("case detail includes linked customer labels", () => {
  assert.match(detailSource, /linkedCustomerLabel/);
  assert.match(detailSource, /noCustomerLinked/);
  assert.match(detailSource, /workspace-case-linked-customer/);
});

test("case detail includes change and unlink customer labels", () => {
  assert.match(detailSource, /changeCustomer/);
  assert.match(detailSource, /unlinkCustomer/);
  assert.match(detailSource, /selectCustomer/);
  assert.match(detailSource, /noCustomer/);
  assert.match(detailSource, /customerLinkError/);
});

test("case detail reuses customers API without duplicating paths", () => {
  assert.match(detailSource, /listCustomers/);
  assert.doesNotMatch(detailSource, /\/api\/v1\/workspaces\/\$\{workspaceId\}\/customers/);
  assert.match(customersApiSource, /export async function listCustomers/);
});
