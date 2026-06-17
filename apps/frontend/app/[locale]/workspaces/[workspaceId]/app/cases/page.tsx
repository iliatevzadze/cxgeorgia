import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppPlaceholder } from "@/components/workspace-app-placeholder";
import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";

type WorkspaceAppCasesPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceAppCasesPage({
  params,
}: WorkspaceAppCasesPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-app-page">
      <WorkspaceAppSectionPanel workspaceId={workspaceId} activeSection="cases">
        <WorkspaceAppPlaceholder section="cases" />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
