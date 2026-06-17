import { setRequestLocale } from "next-intl/server";

import { WorkspaceDetail } from "@/components/workspace-detail";

type WorkspaceDetailPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceDetailPage({
  params,
}: WorkspaceDetailPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-page">
      <WorkspaceDetail workspaceId={workspaceId} />
    </main>
  );
}
