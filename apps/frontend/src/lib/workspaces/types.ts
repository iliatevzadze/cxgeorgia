export type WorkspaceStatus = "active" | "disabled";

export type WorkspaceMemberRole = "owner" | "admin" | "member";

export type WorkspaceMemberStatus = "active" | "removed";

export type WorkspaceRead = {
  id: string;
  name: string;
  slug: string;
  status: WorkspaceStatus;
  created_at: string;
  updated_at: string;
};

export type WorkspaceMembershipRead = {
  id: string;
  workspace_id: string;
  user_id: string;
  role: WorkspaceMemberRole;
  status: WorkspaceMemberStatus;
  created_at: string;
  updated_at: string;
};

export type WorkspaceWithMembershipRead = {
  workspace: WorkspaceRead;
  membership: WorkspaceMembershipRead;
};

export type WorkspaceCreateRequest = {
  name: string;
};
