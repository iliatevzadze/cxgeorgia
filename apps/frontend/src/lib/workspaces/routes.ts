/** Locale-aware frontend workspace routes (next-intl Link paths). */

export const workspaceRoutes = {
  list: () => "/workspaces",
  new: () => "/workspaces/new",
  detail: (workspaceId: string) => `/workspaces/${workspaceId}`,
  memberships: (workspaceId: string) =>
    `/workspaces/${workspaceId}/memberships`,
  app: (workspaceId: string) => `/workspaces/${workspaceId}/app`,
} as const;
