import { setRequestLocale } from "next-intl/server";

import { WorkspaceCreateForm } from "@/components/workspace-create-form";

type NewWorkspacePageProps = {
  params: Promise<{ locale: string }>;
};

export default async function NewWorkspacePage({
  params,
}: NewWorkspacePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main className="page workspace-page">
      <WorkspaceCreateForm />
    </main>
  );
}
