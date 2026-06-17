import { apiRequest } from "@/lib/api/client";

import type { UniversalCaseCreateRequest, UniversalCaseRead } from "./types";

export const casePaths = {
  list: (workspaceId: string) => `/api/v1/workspaces/${workspaceId}/cases`,
  create: (workspaceId: string) => `/api/v1/workspaces/${workspaceId}/cases`,
  detail: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}`,
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
