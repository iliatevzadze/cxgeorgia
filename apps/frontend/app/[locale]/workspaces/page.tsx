import { setRequestLocale } from "next-intl/server";

import { WorkspaceList } from "@/components/workspace-list";

type WorkspacesPageProps = {
  params: Promise<{ locale: string }>;
};

export default async function WorkspacesPage({ params }: WorkspacesPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-page">
      <WorkspaceList />
    </main>
  );
}
