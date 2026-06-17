import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppPlaceholder } from "@/components/workspace-app-placeholder";
import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";

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
        <WorkspaceAppPlaceholder section="dashboard" />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
