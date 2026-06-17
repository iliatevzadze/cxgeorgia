import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";
import { WorkspaceCaseDetail } from "@/components/workspace-case-detail";

type WorkspaceAppCaseDetailPageProps = {
  params: Promise<{ locale: string; workspaceId: string; caseId: string }>;
};

export default async function WorkspaceAppCaseDetailPage({
  params,
}: WorkspaceAppCaseDetailPageProps) {
  const { locale, workspaceId, caseId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-app-page">
      <WorkspaceAppSectionPanel workspaceId={workspaceId} activeSection="cases">
        <WorkspaceCaseDetail workspaceId={workspaceId} caseId={caseId} />
      </WorkspaceAppSectionPanel>
    </main>
  );
}
