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

const requiredNamespaces = ["metadata", "home", "locale"];

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
    "home.notBuiltAuth",
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
