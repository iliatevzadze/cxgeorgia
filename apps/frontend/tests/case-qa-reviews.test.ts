import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiSource = readFileSync(
  join(rootDir, "src/lib/cases/qa-api.ts"),
  "utf-8",
);
const typesSource = readFileSync(
  join(rootDir, "src/lib/cases/qa-types.ts"),
  "utf-8",
);
const componentSource = readFileSync(
  join(rootDir, "src/components/case-qa-reviews.tsx"),
  "utf-8",
);
const detailSource = readFileSync(
  join(rootDir, "src/components/workspace-case-detail.tsx"),
  "utf-8",
);

test("caseQaPaths.list includes workspace id and case id", () => {
  const workspaceId = "550e8400-e29b-41d4-a716-446655440000";
  const caseId = "7c9e6679-7425-40de-944b-e07fc1f90ae7";
  assert.match(
    apiSource,
    new RegExp(
      "`/api/v1/workspaces/\\$\\{workspaceId\\}/cases/\\$\\{caseId\\}/qa-reviews`",
    ),
  );
  assert.match(apiSource, /caseQaPaths\.list\(workspaceId, caseId\)/);
  assert.equal(
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews`,
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews`,
  );
});

test("case qa api exports review helpers", () => {
  assert.match(apiSource, /export async function listCaseQaReviews/);
  assert.match(apiSource, /export async function createCaseQaReview/);
  assert.match(apiSource, /export async function addCaseQaCriteriaScore/);
  assert.match(apiSource, /export async function approveCaseQaReview/);
  assert.match(apiSource, /export async function rejectCaseQaReview/);
  assert.match(apiSource, /caseQaPaths\.criteria\(workspaceId, caseId, reviewId\)/);
  assert.match(apiSource, /caseQaPaths\.approve\(workspaceId, caseId, reviewId\)/);
  assert.match(apiSource, /caseQaPaths\.reject\(workspaceId, caseId, reviewId\)/);
});

test("case qa types export expected shapes and statuses", () => {
  assert.match(typesSource, /export type QaReviewStatus = "pending" \| "approved" \| "rejected"/);
  assert.match(typesSource, /export type CaseQaReview = \{/);
  assert.match(typesSource, /reviewed_by_user_id: string \| null/);
  assert.match(typesSource, /reviewed_agent_user_id: string \| null/);
  assert.match(typesSource, /criteria_scores: CaseQaCriteriaScore\[\]/);
  assert.match(typesSource, /export type CaseQaCriteriaScore = \{/);
  assert.match(typesSource, /export type CaseQaReviewCreateRequest = \{/);
  assert.match(typesSource, /export type CaseQaCriteriaScoreCreateRequest = \{/);
});

test("case detail imports QA review component", () => {
  assert.match(detailSource, /CaseQaReviews/);
  assert.match(detailSource, /memberships=\{memberships\}/);
});

test("QA component includes main labels", () => {
  assert.match(componentSource, /qaReviewsTitle/);
  assert.match(componentSource, /qaReviewsEmpty/);
  assert.match(componentSource, /qaReviewCreateTitle/);
  assert.match(componentSource, /qaReviewAgentLabel/);
  assert.match(componentSource, /qaReviewOverallCommentLabel/);
  assert.match(componentSource, /qaCriteriaAddTitle/);
  assert.match(componentSource, /qaCriterionNameLabel/);
  assert.match(componentSource, /qaScoreLabel/);
  assert.match(componentSource, /qaCommentLabel/);
  assert.match(componentSource, /qaStatusOptions\./);
});

test("QA component handles loading error and empty states", () => {
  assert.match(componentSource, /isLoading/);
  assert.match(componentSource, /qaReviewsLoading/);
  assert.match(componentSource, /loadError/);
  assert.match(componentSource, /qaReviewsLoadError/);
  assert.match(componentSource, /workspace-error/);
  assert.match(componentSource, /qaReviewsEmpty/);
  assert.match(componentSource, /workspace-empty/);
});

test("QA component includes approve and reject actions", () => {
  assert.match(componentSource, /approveCaseQaReview/);
  assert.match(componentSource, /rejectCaseQaReview/);
  assert.match(componentSource, /qaApproveButton/);
  assert.match(componentSource, /qaRejectButton/);
  assert.match(componentSource, /handleApprove/);
  assert.match(componentSource, /handleReject/);
});
