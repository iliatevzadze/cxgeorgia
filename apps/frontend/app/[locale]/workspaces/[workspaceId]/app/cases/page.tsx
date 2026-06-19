import { Suspense } from "react";
import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";
import { WorkspaceCasesList } from "@/components/workspace-cases-list";

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
        <Suspense fallback={null}>
          <WorkspaceCasesList workspaceId={workspaceId} />
        </Suspense>
      </WorkspaceAppSectionPanel>
    </main>
  );
}
