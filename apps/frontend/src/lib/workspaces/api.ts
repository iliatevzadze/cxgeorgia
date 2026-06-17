import { apiRequest } from "@/lib/api/client";

import type {
  WorkspaceCreateRequest,
  WorkspaceMembershipRead,
  WorkspaceRead,
  WorkspaceWithMembershipRead,
} from "./types";

export const workspacePaths = {
  list: () => "/api/v1/workspaces",
  create: () => "/api/v1/workspaces",
  detail: (workspaceId: string) => `/api/v1/workspaces/${workspaceId}`,
  memberships: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/memberships`,
} as const;

export async function createWorkspace(
  input: WorkspaceCreateRequest,
  token: string,
): Promise<WorkspaceWithMembershipRead> {
  return apiRequest<WorkspaceWithMembershipRead>(workspacePaths.create(), {
    method: "POST",
    body: { name: input.name.trim() },
    token,
  });
}

export async function listWorkspaces(
  token: string,
): Promise<WorkspaceWithMembershipRead[]> {
  return apiRequest<WorkspaceWithMembershipRead[]>(workspacePaths.list(), {
    token,
  });
}

export async function getWorkspace(
  workspaceId: string,
  token: string,
): Promise<WorkspaceRead> {
  return apiRequest<WorkspaceRead>(workspacePaths.detail(workspaceId), {
    token,
  });
}

export async function listWorkspaceMemberships(
  workspaceId: string,
  token: string,
): Promise<WorkspaceMembershipRead[]> {
  return apiRequest<WorkspaceMembershipRead[]>(
    workspacePaths.memberships(workspaceId),
    { token },
  );
}
