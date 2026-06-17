/**
 * Token storage uses browser localStorage and is validated in browser/E2E flows.
 * These tests cover the storage key contract used by the auth module.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const tokenStorageSource = readFileSync(
  join(rootDir, "src/lib/auth/token-storage.ts"),
  "utf-8",
);

test("token storage uses a stable localStorage key", () => {
  assert.match(tokenStorageSource, /cx_access_token/);
});

test("token storage exposes get, set, and clear helpers", () => {
  assert.match(tokenStorageSource, /export function getAccessToken/);
  assert.match(tokenStorageSource, /export function setAccessToken/);
  assert.match(tokenStorageSource, /export function clearAccessToken/);
});
