import { apiRequest } from "@/lib/api/client";

import type { AgentCaseMetric, AgentShift, CaseMetricsFilters } from "./types";

export const agentWorkforcePaths = {
  clockIn: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/agent-workforce/clock-in`,
  clockOut: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/agent-workforce/clock-out`,
  myActiveShift: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/agent-workforce/me/active-shift`,
  activeShifts: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/agent-workforce/active-shifts`,
  caseMetrics: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/agent-workforce/case-metrics`,
} as const;

export async function clockInAgentShift(
  workspaceId: string,
  token: string,
): Promise<AgentShift> {
  return apiRequest<AgentShift>(agentWorkforcePaths.clockIn(workspaceId), {
    method: "POST",
    token,
  });
}

export async function clockOutAgentShift(
  workspaceId: string,
  token: string,
): Promise<AgentShift> {
  return apiRequest<AgentShift>(agentWorkforcePaths.clockOut(workspaceId), {
    method: "POST",
    token,
  });
}

export async function getMyActiveAgentShift(
  workspaceId: string,
  token: string,
): Promise<AgentShift | null> {
  return apiRequest<AgentShift | null>(
    agentWorkforcePaths.myActiveShift(workspaceId),
    { token },
  );
}

export async function listActiveAgentShifts(
  workspaceId: string,
  token: string,
): Promise<AgentShift[]> {
  return apiRequest<AgentShift[]>(
    agentWorkforcePaths.activeShifts(workspaceId),
    { token },
  );
}

export async function listAgentCaseMetrics(
  workspaceId: string,
  token: string,
  filters: CaseMetricsFilters = {},
): Promise<AgentCaseMetric[]> {
  const params = new URLSearchParams();
  if (filters.user_id?.trim()) {
    params.set("user_id", filters.user_id.trim());
  }
  if (filters.case_id?.trim()) {
    params.set("case_id", filters.case_id.trim());
  }
  const query = params.toString();
  const path = query
    ? `${agentWorkforcePaths.caseMetrics(workspaceId)}?${query}`
    : agentWorkforcePaths.caseMetrics(workspaceId);

  return apiRequest<AgentCaseMetric[]>(path, { token });
}
