import { apiRequest } from "@/lib/api/client";

import type { OperationsDashboardRead } from "./types";

export const operationsPaths = {
  dashboard: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/operations/dashboard`,
} as const;

export async function getOperationsDashboard(
  workspaceId: string,
  token: string,
): Promise<OperationsDashboardRead> {
  return apiRequest<OperationsDashboardRead>(
    operationsPaths.dashboard(workspaceId),
    { token },
  );
}
