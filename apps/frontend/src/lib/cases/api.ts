import { apiRequest } from "@/lib/api/client";

import type {
  CaseActivityRead,
  CaseCommentCreateRequest,
  CaseCommentDeleteResponse,
  CaseCommentRead,
  UniversalCaseCreateRequest,
  UniversalCaseDeleteResponse,
  UniversalCaseRead,
  UniversalCaseUpdateRequest,
} from "./types";

export const casePaths = {
  list: (workspaceId: string) => `/api/v1/workspaces/${workspaceId}/cases`,
  create: (workspaceId: string) => `/api/v1/workspaces/${workspaceId}/cases`,
  detail: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}`,
  comments: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/comments`,
  commentDetail: (workspaceId: string, caseId: string, commentId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/comments/${commentId}`,
  activities: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/activities`,
} as const;

export async function listCases(
  workspaceId: string,
  token: string,
): Promise<UniversalCaseRead[]> {
  return apiRequest<UniversalCaseRead[]>(casePaths.list(workspaceId), {
    token,
  });
}

export async function createCase(
  workspaceId: string,
  payload: UniversalCaseCreateRequest,
  token: string,
): Promise<UniversalCaseRead> {
  return apiRequest<UniversalCaseRead>(casePaths.create(workspaceId), {
    method: "POST",
    body: payload,
    token,
  });
}

export async function getCase(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<UniversalCaseRead> {
  return apiRequest<UniversalCaseRead>(
    casePaths.detail(workspaceId, caseId),
    { token },
  );
}

export async function updateCase(
  workspaceId: string,
  caseId: string,
  payload: UniversalCaseUpdateRequest,
  token: string,
): Promise<UniversalCaseRead> {
  return apiRequest<UniversalCaseRead>(
    casePaths.detail(workspaceId, caseId),
    {
      method: "PATCH",
      body: payload,
      token,
    },
  );
}

export async function deleteCase(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<UniversalCaseDeleteResponse> {
  return apiRequest<UniversalCaseDeleteResponse>(
    casePaths.detail(workspaceId, caseId),
    {
      method: "DELETE",
      token,
    },
  );
}

export async function listCaseComments(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<CaseCommentRead[]> {
  return apiRequest<CaseCommentRead[]>(
    casePaths.comments(workspaceId, caseId),
    { token },
  );
}

export async function createCaseComment(
  workspaceId: string,
  caseId: string,
  payload: CaseCommentCreateRequest,
  token: string,
): Promise<CaseCommentRead> {
  return apiRequest<CaseCommentRead>(
    casePaths.comments(workspaceId, caseId),
    {
      method: "POST",
      body: payload,
      token,
    },
  );
}

export async function deleteCaseComment(
  workspaceId: string,
  caseId: string,
  commentId: string,
  token: string,
): Promise<CaseCommentDeleteResponse> {
  return apiRequest<CaseCommentDeleteResponse>(
    casePaths.commentDetail(workspaceId, caseId, commentId),
    {
      method: "DELETE",
      token,
    },
  );
}

export async function listCaseActivities(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<CaseActivityRead[]> {
  return apiRequest<CaseActivityRead[]>(
    casePaths.activities(workspaceId, caseId),
    { token },
  );
}
