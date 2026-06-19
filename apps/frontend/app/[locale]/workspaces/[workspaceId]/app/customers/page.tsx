import { setRequestLocale } from "next-intl/server";

import { WorkspaceCustomers } from "@/components/workspace-customers";
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
        <WorkspaceCustomers workspaceId={workspaceId} />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
