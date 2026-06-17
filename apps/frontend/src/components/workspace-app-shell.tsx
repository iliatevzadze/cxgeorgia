"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Link } from "@/i18n/navigation";

import { useAuth } from "@/hooks/use-auth";
import { useWorkspace } from "@/hooks/use-workspace";
import type { WorkspaceAppSection } from "@/lib/workspaces/app-sections";
import { workspaceRoutes } from "@/lib/workspaces/routes";

type WorkspaceAppShellProps = {
  workspaceId: string;
  activeSection: WorkspaceAppSection;
  children: ReactNode;
};

type AppNavItemProps = {
  href: string;
  active: boolean;
  children: ReactNode;
};

function AppNavItem({ href, active, children }: AppNavItemProps) {
  return (
    <Link
      href={href}
      className={`workspace-app-nav-item${active ? " is-active" : ""}`}
      aria-current={active ? "page" : undefined}
    >
      {children}
    </Link>
  );
}

export function WorkspaceAppShell({
  workspaceId,
  activeSection,
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
            <AppNavItem
              href={workspaceRoutes.appHome(workspaceId)}
              active={activeSection === "home"}
            >
              {tNav("home")}
            </AppNavItem>
            <AppNavItem
              href={workspaceRoutes.appDashboard(workspaceId)}
              active={activeSection === "dashboard"}
            >
              {tNav("dashboard")}
            </AppNavItem>
            <AppNavItem
              href={workspaceRoutes.appCases(workspaceId)}
              active={activeSection === "cases"}
            >
              {tNav("cases")}
            </AppNavItem>
            <AppNavItem
              href={workspaceRoutes.appCustomers(workspaceId)}
              active={activeSection === "customers"}
            >
              {tNav("customers")}
            </AppNavItem>
            <AppNavItem
              href={workspaceRoutes.appSettings(workspaceId)}
              active={activeSection === "settings"}
            >
              {tNav("settings")}
            </AppNavItem>
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
