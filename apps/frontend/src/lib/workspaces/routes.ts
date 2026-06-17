/** Locale-aware frontend workspace routes (next-intl Link paths). */

export const workspaceRoutes = {
  list: () => "/workspaces",
  new: () => "/workspaces/new",
  detail: (workspaceId: string) => `/workspaces/${workspaceId}`,
  memberships: (workspaceId: string) =>
    `/workspaces/${workspaceId}/memberships`,
  app: (workspaceId: string) => `/workspaces/${workspaceId}/app`,
  appHome: (workspaceId: string) => `/workspaces/${workspaceId}/app`,
  appDashboard: (workspaceId: string) =>
    `/workspaces/${workspaceId}/app/dashboard`,
  appCases: (workspaceId: string) => `/workspaces/${workspaceId}/app/cases`,
  appCustomers: (workspaceId: string) =>
    `/workspaces/${workspaceId}/app/customers`,
  appSettings: (workspaceId: string) =>
    `/workspaces/${workspaceId}/app/settings`,
} as const;
