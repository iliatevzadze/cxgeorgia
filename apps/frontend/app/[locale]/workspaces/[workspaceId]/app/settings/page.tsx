import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppPlaceholder } from "@/components/workspace-app-placeholder";
import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";

type WorkspaceAppSettingsPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceAppSettingsPage({
  params,
}: WorkspaceAppSettingsPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-app-page">
      <WorkspaceAppSectionPanel
        workspaceId={workspaceId}
        activeSection="settings"
      >
        <WorkspaceAppPlaceholder section="settings" />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
