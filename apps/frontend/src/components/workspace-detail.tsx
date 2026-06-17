"use client";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { RequireAuth } from "@/components/require-auth";
import { useWorkspace } from "@/hooks/use-workspace";
import { workspaceRoutes } from "@/lib/workspaces/routes";

type WorkspaceDetailProps = {
  workspaceId: string;
};

function WorkspaceDetailContent({ workspaceId }: WorkspaceDetailProps) {
  const t = useTranslations("workspaces.detail");
  const { workspace, membership, isLoading, errorMessage } =
    useWorkspace(workspaceId);

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (errorMessage || !workspace) {
    return (
      <section className="workspace-panel">
        <p className="workspace-error" role="alert">
          {errorMessage ?? t("error")}
        </p>
        <p className="auth-form-footer">
          <Link href={workspaceRoutes.list()}>{t("backToList")}</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="workspace-panel">
      <h1>{t("title")}</h1>
      <p className="workspace-description">{t("description")}</p>

      <dl className="account-details">
        <div>
          <dt>{t("nameLabel")}</dt>
          <dd>{workspace.name}</dd>
        </div>
        <div>
          <dt>{t("slugLabel")}</dt>
          <dd>{workspace.slug}</dd>
        </div>
        <div>
          <dt>{t("statusLabel")}</dt>
          <dd>{workspace.status}</dd>
        </div>
        <div>
          <dt>{t("roleLabel")}</dt>
          <dd>{membership?.role ?? "—"}</dd>
        </div>
      </dl>

      <p className="workspace-actions">
        <Link
          href={workspaceRoutes.app(workspace.id)}
          className="workspace-button-link"
        >
          {t("openAppLink")}
        </Link>
        <Link href={workspaceRoutes.memberships(workspace.id)}>
          {t("membershipsLink")}
        </Link>
        <Link href={workspaceRoutes.list()}>{t("backToList")}</Link>
      </p>
    </section>
  );
}

export function WorkspaceDetail({ workspaceId }: WorkspaceDetailProps) {
  return (
    <RequireAuth>
      <WorkspaceDetailContent workspaceId={workspaceId} />
    </RequireAuth>
  );
}
