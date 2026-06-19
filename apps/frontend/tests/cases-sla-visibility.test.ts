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
const listSource = readFileSync(
  join(rootDir, "src/components/workspace-cases-list.tsx"),
  "utf-8",
);
const detailSource = readFileSync(
  join(rootDir, "src/components/workspace-case-detail.tsx"),
  "utf-8",
);
const enMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
);
const kaMessages = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
);

test("UniversalCaseRead includes SLA fields", () => {
  const readStart = typesSource.indexOf("export type UniversalCaseRead");
  const readEnd = typesSource.indexOf("export type UniversalCaseCreateRequest");
  const readBlock = typesSource.slice(readStart, readEnd);
  assert.match(readBlock, /first_response_due_at: string \| null/);
  assert.match(readBlock, /first_response_at: string \| null/);
  assert.match(readBlock, /resolution_due_at: string \| null/);
  assert.match(readBlock, /resolved_at: string \| null/);
  assert.match(readBlock, /sla_status: CaseSlaStatus \| null/);
});

test("SLA status union includes on_track, at_risk and breached", () => {
  assert.match(
    typesSource,
    /export type CaseSlaStatus = "on_track" \| "at_risk" \| "breached"/,
  );
});

test("case list includes SLA status labels and badge references", () => {
  assert.match(listSource, /slaStatusLabel/);
  assert.match(listSource, /workspace-case-sla-badge/);
  assert.match(listSource, /slaStatusOptions/);
  assert.match(listSource, /notSet/);
  assert.match(listSource, /item\.sla_status/);
});

test("case detail includes SLA section labels", () => {
  assert.match(detailSource, /workspace-case-sla-panel/);
  assert.match(detailSource, /slaTitle/);
  assert.match(detailSource, /slaStatusLabel/);
  assert.match(detailSource, /workspace-case-sla-badge/);
});

test("case detail includes all SLA timestamp labels", () => {
  assert.match(detailSource, /firstResponseDueLabel/);
  assert.match(detailSource, /firstResponseAtLabel/);
  assert.match(detailSource, /resolutionDueLabel/);
  assert.match(detailSource, /resolvedAtLabel/);
  assert.match(detailSource, /first_response_due_at/);
  assert.match(detailSource, /first_response_at/);
  assert.match(detailSource, /resolution_due_at/);
  assert.match(detailSource, /resolved_at/);
});

test("null SLA values use Not set fallback", () => {
  assert.match(detailSource, /formatOptionalDateTime/);
  assert.match(detailSource, /t\("notSet"\)/);
  assert.match(listSource, /formatSlaStatusLabel/);
});

test("SLA i18n keys are aligned in en and ka", () => {
  const enCases = enMessages.workspaces.app.cases;
  const kaCases = kaMessages.workspaces.app.cases;
  const enDetail = enCases.detail;
  const kaDetail = kaCases.detail;

  assert.equal(enCases.slaStatusLabel, "SLA status");
  assert.equal(kaCases.slaStatusLabel, "SLA სტატუსი");
  assert.equal(enCases.notSet, "Not set");
  assert.equal(kaCases.notSet, "არ არის დაყენებული");
  assert.deepEqual(enCases.slaStatusOptions, {
    on_track: "On track",
    at_risk: "At risk",
    breached: "Breached",
  });
  assert.deepEqual(kaCases.slaStatusOptions, {
    on_track: "გრაფიკზე",
    at_risk: "რისკში",
    breached: "დარღვეული",
  });

  assert.equal(enDetail.slaTitle, "SLA");
  assert.equal(kaDetail.slaTitle, "SLA");
  assert.equal(enDetail.firstResponseDueLabel, "First response due");
  assert.equal(kaDetail.firstResponseDueLabel, "პირველი პასუხის ვადა");
  assert.equal(enDetail.firstResponseAtLabel, "First response at");
  assert.equal(kaDetail.firstResponseAtLabel, "პირველი პასუხის დრო");
  assert.equal(enDetail.resolutionDueLabel, "Resolution due");
  assert.equal(kaDetail.resolutionDueLabel, "გადაწყვეტის ვადა");
  assert.equal(enDetail.resolvedAtLabel, "Resolved at");
  assert.equal(kaDetail.resolvedAtLabel, "გადაწყვეტის დრო");
});
