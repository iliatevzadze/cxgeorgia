import { setRequestLocale } from "next-intl/server";

import { WorkspaceAppPanel } from "@/components/workspace-app-panel";

type WorkspaceAppPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceAppPage({
  params,
}: WorkspaceAppPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-app-page">
      <WorkspaceAppPanel workspaceId={workspaceId} />
    </main>
  );
}
