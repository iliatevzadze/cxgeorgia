import { apiRequest } from "@/lib/api/client";

import type { UniversalCaseRead } from "./types";

export const casePaths = {
  list: (workspaceId: string) => `/api/v1/workspaces/${workspaceId}/cases`,
} as const;

export async function listCases(
  workspaceId: string,
  token: string,
): Promise<UniversalCaseRead[]> {
  return apiRequest<UniversalCaseRead[]>(casePaths.list(workspaceId), {
    token,
  });
}
