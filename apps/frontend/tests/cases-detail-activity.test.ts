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

test("case detail renders activity timeline section", () => {
  assert.match(detailSource, /workspace-case-activities-panel/);
  assert.match(detailSource, /activitiesTitle/);
  assert.match(detailSource, /listCaseActivities/);
});

test("case detail activity section includes loading empty and error states", () => {
  assert.match(detailSource, /activitiesLoading/);
  assert.match(detailSource, /activitiesEmpty/);
  assert.match(detailSource, /activitiesLoadError/);
});

test("case detail activity labels use activity type translations", () => {
  assert.match(detailSource, /activityTypeLabels\.\$\{activity\.activity_type\}/);
});

test("case detail formats activity metadata summaries", () => {
  assert.match(detailSource, /getActivityMetadataSummary/);
  assert.match(detailSource, /formatActivityMetadataSummary/);
});

test("case detail keeps page usable when activity fetch fails", () => {
  assert.match(detailSource, /commentsTitle/);
  assert.match(detailSource, /updateTitle/);
  assert.doesNotMatch(
    detailSource,
    /if \(activitiesLoadError[\s\S]*return/,
  );
});
