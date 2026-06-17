import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");

function collectKeys(
  value: unknown,
  prefix = "",
): string[] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return prefix ? [prefix] : [];
  }

  return Object.entries(value as Record<string, unknown>).flatMap(
    ([key, nested]) => {
      const path = prefix ? `${prefix}.${key}` : key;
      if (
        nested !== null &&
        typeof nested === "object" &&
        !Array.isArray(nested)
      ) {
        return collectKeys(nested, path);
      }
      return [path];
    },
  );
}

const ka = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
) as Record<string, unknown>;
const en = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
) as Record<string, unknown>;

const kaKeys = collectKeys(ka).sort();
const enKeys = collectKeys(en).sort();

const requiredNamespaces = ["metadata", "home", "locale", "auth", "workspaces"];

test("both locale files include required top-level namespaces", () => {
  for (const namespace of requiredNamespaces) {
    assert.ok(namespace in ka, `ka.json missing namespace: ${namespace}`);
    assert.ok(namespace in en, `en.json missing namespace: ${namespace}`);
  }
});

test("ka.json and en.json have matching keys", () => {
  assert.deepEqual(
    kaKeys,
    enKeys,
    `Key mismatch.\nOnly in ka: ${kaKeys.filter((k) => !enKeys.includes(k)).join(", ")}\nOnly in en: ${enKeys.filter((k) => !kaKeys.includes(k)).join(", ")}`,
  );
});

test("required home keys exist in both locales", () => {
  const requiredHomeKeys = [
    "home.phase",
    "home.title",
    "home.subtitle",
    "home.description",
    "home.statusLabel",
    "home.statusValue",
    "home.backendLabel",
    "home.backendValue",
    "home.infrastructureLabel",
    "home.infrastructureValue",
    "home.notBuiltTitle",
    "home.notBuiltDashboard",
    "home.notBuiltCases",
    "home.notBuiltIntegrations",
    "home.language",
  ];

  for (const key of requiredHomeKeys) {
    assert.ok(kaKeys.includes(key), `ka.json missing key: ${key}`);
    assert.ok(enKeys.includes(key), `en.json missing key: ${key}`);
  }
});

test("required workspace keys exist in both locales", () => {
  const requiredWorkspaceKeys = [
    "workspaces.nav.myWorkspaces",
    "workspaces.nav.createWorkspace",
    "workspaces.list.title",
    "workspaces.list.description",
    "workspaces.list.empty",
    "workspaces.list.createLink",
    "workspaces.list.loading",
    "workspaces.list.error",
    "workspaces.list.roleLabel",
    "workspaces.list.statusLabel",
    "workspaces.list.openLink",
    "workspaces.create.title",
    "workspaces.create.description",
    "workspaces.create.nameLabel",
    "workspaces.create.namePlaceholder",
    "workspaces.create.submit",
    "workspaces.create.success",
    "workspaces.create.error",
    "workspaces.create.backToList",
    "workspaces.create.openWorkspace",
    "workspaces.detail.title",
    "workspaces.detail.description",
    "workspaces.detail.slugLabel",
    "workspaces.detail.statusLabel",
    "workspaces.detail.roleLabel",
    "workspaces.detail.membershipsLink",
    "workspaces.detail.openAppLink",
    "workspaces.detail.backToList",
    "workspaces.detail.loading",
    "workspaces.detail.error",
    "workspaces.memberships.title",
    "workspaces.memberships.description",
    "workspaces.memberships.userId",
    "workspaces.memberships.role",
    "workspaces.memberships.status",
    "workspaces.memberships.loading",
    "workspaces.memberships.error",
    "workspaces.memberships.backToWorkspace",
    "workspaces.common.loading",
    "workspaces.common.loadError",
    "workspaces.common.notFound",
    "workspaces.common.accessDenied",
    "workspaces.app.shell.label",
    "workspaces.app.shell.statusLabel",
    "workspaces.app.shell.roleLabel",
    "workspaces.app.shell.accountNav",
    "workspaces.app.shell.account",
    "workspaces.app.shell.allWorkspaces",
    "workspaces.app.shell.logout",
    "workspaces.app.shell.workspaceDetail",
    "workspaces.app.shell.backToWorkspaces",
    "workspaces.app.nav.label",
    "workspaces.app.nav.home",
    "workspaces.app.nav.dashboard",
    "workspaces.app.nav.cases",
    "workspaces.app.nav.customers",
    "workspaces.app.nav.settings",
    "workspaces.app.home.title",
    "workspaces.app.home.description",
    "workspaces.app.home.ready",
    "workspaces.app.home.notBuiltTitle",
    "workspaces.app.home.notBuiltDashboard",
    "workspaces.app.home.notBuiltCases",
    "workspaces.app.home.notBuiltCustomers",
    "workspaces.app.home.notBuiltIntegrations",
  ];

  for (const key of requiredWorkspaceKeys) {
    assert.ok(kaKeys.includes(key), `ka.json missing key: ${key}`);
    assert.ok(enKeys.includes(key), `en.json missing key: ${key}`);
  }
});
