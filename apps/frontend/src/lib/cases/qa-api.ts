import { apiRequest } from "@/lib/api/client";

import type {
  CaseQaCriteriaScoreCreateRequest,
  CaseQaReview,
  CaseQaReviewCreateRequest,
} from "./qa-types";

export const caseQaPaths = {
  list: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews`,
  create: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews`,
  criteria: (workspaceId: string, caseId: string, reviewId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews/${reviewId}/criteria`,
  approve: (workspaceId: string, caseId: string, reviewId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews/${reviewId}/approve`,
  reject: (workspaceId: string, caseId: string, reviewId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/qa-reviews/${reviewId}/reject`,
} as const;

export async function listCaseQaReviews(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<CaseQaReview[]> {
  return apiRequest<CaseQaReview[]>(caseQaPaths.list(workspaceId, caseId), {
    token,
  });
}

export async function createCaseQaReview(
  workspaceId: string,
  caseId: string,
  payload: CaseQaReviewCreateRequest,
  token: string,
): Promise<CaseQaReview> {
  return apiRequest<CaseQaReview>(caseQaPaths.create(workspaceId, caseId), {
    method: "POST",
    body: payload,
    token,
  });
}

export async function addCaseQaCriteriaScore(
  workspaceId: string,
  caseId: string,
  reviewId: string,
  payload: CaseQaCriteriaScoreCreateRequest,
  token: string,
): Promise<CaseQaReview> {
  return apiRequest<CaseQaReview>(
    caseQaPaths.criteria(workspaceId, caseId, reviewId),
    {
      method: "POST",
      body: payload,
      token,
    },
  );
}

export async function approveCaseQaReview(
  workspaceId: string,
  caseId: string,
  reviewId: string,
  token: string,
): Promise<CaseQaReview> {
  return apiRequest<CaseQaReview>(
    caseQaPaths.approve(workspaceId, caseId, reviewId),
    {
      method: "POST",
      token,
    },
  );
}

export async function rejectCaseQaReview(
  workspaceId: string,
  caseId: string,
  reviewId: string,
  token: string,
): Promise<CaseQaReview> {
  return apiRequest<CaseQaReview>(
    caseQaPaths.reject(workspaceId, caseId, reviewId),
    {
      method: "POST",
      token,
    },
  );
}
