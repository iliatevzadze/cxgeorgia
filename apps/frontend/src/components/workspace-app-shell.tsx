"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Link } from "@/i18n/navigation";

import { useAuth } from "@/hooks/use-auth";
import { useWorkspace } from "@/hooks/use-workspace";
import { workspaceRoutes } from "@/lib/workspaces/routes";

type WorkspaceAppShellProps = {
  workspaceId: string;
  children: ReactNode;
};

export function WorkspaceAppShell({
  workspaceId,
  children,
}: WorkspaceAppShellProps) {
  const t = useTranslations("workspaces.app.shell");
  const tNav = useTranslations("workspaces.app.nav");
  const tCommon = useTranslations("workspaces.common");
  const { logout } = useAuth();
  const { workspace, membership, isLoading, errorMessage } =
    useWorkspace(workspaceId);

  if (isLoading) {
    return <p className="workspace-status">{tCommon("loading")}</p>;
  }

  if (errorMessage || !workspace) {
    return (
      <section className="workspace-panel workspace-app-error">
        <p className="workspace-error" role="alert">
          {errorMessage ?? tCommon("loadError")}
        </p>
        <p className="auth-form-footer">
          <Link href={workspaceRoutes.list()}>{t("backToWorkspaces")}</Link>
        </p>
      </section>
    );
  }

  return (
    <div className="workspace-app">
      <header className="workspace-app-header">
        <div className="workspace-app-brand">
          <p className="workspace-app-eyebrow">{t("label")}</p>
          <h1>{workspace.name}</h1>
          <p className="workspace-app-meta">
            {workspace.slug} · {t("statusLabel")}: {workspace.status}
            {membership ? ` · ${t("roleLabel")}: ${membership.role}` : null}
          </p>
        </div>
        <nav className="workspace-app-account-nav" aria-label={t("accountNav")}>
          <Link href="/account">{t("account")}</Link>
          <Link href={workspaceRoutes.list()}>{t("allWorkspaces")}</Link>
          <button type="button" className="link-button" onClick={logout}>
            {t("logout")}
          </button>
        </nav>
      </header>

      <div className="workspace-app-body">
        <aside className="workspace-app-sidebar">
          <nav className="workspace-app-module-nav" aria-label={tNav("label")}>
            <span className="workspace-app-nav-item is-active">
              {tNav("home")}
            </span>
            <span className="workspace-app-nav-item is-disabled">
              {tNav("dashboard")}
            </span>
            <span className="workspace-app-nav-item is-disabled">
              {tNav("cases")}
            </span>
            <span className="workspace-app-nav-item is-disabled">
              {tNav("customers")}
            </span>
            <span className="workspace-app-nav-item is-disabled">
              {tNav("settings")}
            </span>
          </nav>

          <div className="workspace-app-sidebar-links">
            <Link href={workspaceRoutes.detail(workspaceId)}>
              {t("workspaceDetail")}
            </Link>
            <Link href={workspaceRoutes.list()}>{t("backToWorkspaces")}</Link>
          </div>
        </aside>

        <main className="workspace-app-main">{children}</main>
      </div>
    </div>
  );
}
