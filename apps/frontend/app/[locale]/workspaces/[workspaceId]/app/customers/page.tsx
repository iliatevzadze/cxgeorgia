import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppPlaceholder } from "@/components/workspace-app-placeholder";
import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";

type WorkspaceAppCustomersPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceAppCustomersPage({
  params,
}: WorkspaceAppCustomersPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-app-page">
      <WorkspaceAppSectionPanel
        workspaceId={workspaceId}
        activeSection="customers"
      >
        <WorkspaceAppPlaceholder section="customers" />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
