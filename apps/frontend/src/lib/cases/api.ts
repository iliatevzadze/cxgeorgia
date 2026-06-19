import { apiRequest } from "@/lib/api/client";

import type {
  CaseActivityRead,
  CaseCommentCreateRequest,
  CaseCommentDeleteResponse,
  CaseCommentRead,
  CaseCommentUpdateRequest,
  CaseTag,
  CaseTagCreateInput,
  CaseTagDetachResponse,
  UniversalCaseCreateRequest,
  UniversalCaseDeleteResponse,
  UniversalCaseRead,
  UniversalCaseUpdateRequest,
  CaseListFilters,
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
  caseTags: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/tags`,
  caseTagDetail: (workspaceId: string, caseId: string, tagId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/tags/${tagId}`,
  workspaceCaseTags: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/case-tags`,
} as const;

export async function listCases(
  workspaceId: string,
  token: string,
  filters: CaseListFilters = {},
): Promise<UniversalCaseRead[]> {
  const params = new URLSearchParams();
  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.priority) {
    params.set("priority", filters.priority);
  }
  if (filters.source) {
    params.set("source", filters.source);
  }
  if (filters.assigned_to_user_id?.trim()) {
    params.set("assigned_to_user_id", filters.assigned_to_user_id.trim());
  }
  if (filters.customer_id?.trim()) {
    params.set("customer_id", filters.customer_id.trim());
  }
  if (filters.sla_status) {
    params.set("sla_status", filters.sla_status);
  }
  const query = params.toString();
  const path = query
    ? `${casePaths.list(workspaceId)}?${query}`
    : casePaths.list(workspaceId);

  return apiRequest<UniversalCaseRead[]>(path, { token });
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

export async function updateCaseComment(
  workspaceId: string,
  caseId: string,
  commentId: string,
  payload: CaseCommentUpdateRequest,
  token: string,
): Promise<CaseCommentRead> {
  return apiRequest<CaseCommentRead>(
    casePaths.commentDetail(workspaceId, caseId, commentId),
    {
      method: "PATCH",
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

export async function listWorkspaceCaseTags(
  workspaceId: string,
  token: string,
): Promise<CaseTag[]> {
  return apiRequest<CaseTag[]>(casePaths.workspaceCaseTags(workspaceId), {
    token,
  });
}

export async function createWorkspaceCaseTag(
  workspaceId: string,
  payload: CaseTagCreateInput,
  token: string,
): Promise<CaseTag> {
  return apiRequest<CaseTag>(casePaths.workspaceCaseTags(workspaceId), {
    method: "POST",
    body: payload,
    token,
  });
}

export async function listCaseTags(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<CaseTag[]> {
  return apiRequest<CaseTag[]>(casePaths.caseTags(workspaceId, caseId), {
    token,
  });
}

export async function attachCaseTag(
  workspaceId: string,
  caseId: string,
  tagId: string,
  token: string,
): Promise<CaseTag> {
  return apiRequest<CaseTag>(
    casePaths.caseTagDetail(workspaceId, caseId, tagId),
    {
      method: "POST",
      token,
    },
  );
}

export async function detachCaseTag(
  workspaceId: string,
  caseId: string,
  tagId: string,
  token: string,
): Promise<CaseTagDetachResponse> {
  return apiRequest<CaseTagDetachResponse>(
    casePaths.caseTagDetail(workspaceId, caseId, tagId),
    {
      method: "DELETE",
      token,
    },
  );
}
