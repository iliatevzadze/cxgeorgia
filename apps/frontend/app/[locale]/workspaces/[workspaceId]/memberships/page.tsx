import { setRequestLocale } from "next-intl/server";

import { WorkspaceMemberships } from "@/components/workspace-memberships";

type WorkspaceMembershipsPageProps = {
  params: Promise<{ locale: string; workspaceId: string }>;
};

export default async function WorkspaceMembershipsPage({
  params,
}: WorkspaceMembershipsPageProps) {
  const { locale, workspaceId } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-page">
      <WorkspaceMemberships workspaceId={workspaceId} />
    </main>
  );
}
