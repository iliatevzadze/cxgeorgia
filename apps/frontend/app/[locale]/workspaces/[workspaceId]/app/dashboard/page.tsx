import { setRequestLocale } from "next-intl/server";

import { AgentWorkforcePanel } from "@/components/agent-workforce-panel";
import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";
import { WorkspaceOperationsDashboard } from "@/components/workspace-operations-dashboard";

type WorkspaceAppDashboardPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceAppDashboardPage({
  params,
}: WorkspaceAppDashboardPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-app-page">
      <WorkspaceAppSectionPanel
        workspaceId={workspaceId}
        activeSection="dashboard"
      >
        <WorkspaceOperationsDashboard workspaceId={workspaceId} />
        <AgentWorkforcePanel workspaceId={workspaceId} />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
