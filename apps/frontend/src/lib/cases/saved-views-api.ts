import { apiRequest } from "@/lib/api/client";

import type {
  CaseListViewCreateRequest,
  CaseListViewDeleteResponse,
  CaseListViewRead,
  CaseListViewUpdateRequest,
} from "./saved-views-types";

export const caseListViewPaths = {
  list: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/case-list-views`,
  create: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/case-list-views`,
  detail: (workspaceId: string, viewId: string) =>
    `/api/v1/workspaces/${workspaceId}/case-list-views/${viewId}`,
} as const;

export async function listCaseListViews(
  workspaceId: string,
  token: string,
): Promise<CaseListViewRead[]> {
  return apiRequest<CaseListViewRead[]>(caseListViewPaths.list(workspaceId), {
    token,
  });
}

export async function createCaseListView(
  workspaceId: string,
  body: CaseListViewCreateRequest,
  token: string,
): Promise<CaseListViewRead> {
  return apiRequest<CaseListViewRead>(caseListViewPaths.create(workspaceId), {
    method: "POST",
    body,
    token,
  });
}

export async function getCaseListView(
  workspaceId: string,
  viewId: string,
  token: string,
): Promise<CaseListViewRead> {
  return apiRequest<CaseListViewRead>(
    caseListViewPaths.detail(workspaceId, viewId),
    { token },
  );
}

export async function updateCaseListView(
  workspaceId: string,
  viewId: string,
  body: CaseListViewUpdateRequest,
  token: string,
): Promise<CaseListViewRead> {
  return apiRequest<CaseListViewRead>(
    caseListViewPaths.detail(workspaceId, viewId),
    {
      method: "PATCH",
      body,
      token,
    },
  );
}

export async function deleteCaseListView(
  workspaceId: string,
  viewId: string,
  token: string,
): Promise<CaseListViewDeleteResponse> {
  return apiRequest<CaseListViewDeleteResponse>(
    caseListViewPaths.detail(workspaceId, viewId),
    {
      method: "DELETE",
      token,
    },
  );
}
