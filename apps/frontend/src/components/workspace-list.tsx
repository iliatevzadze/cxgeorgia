"use client";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { RequireAuth } from "@/components/require-auth";
import { useWorkspaces } from "@/hooks/use-workspaces";

function WorkspaceListContent() {
  const t = useTranslations("workspaces.list");
  const { items, isLoading, error } = useWorkspaces();

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (error) {
    return <p className="workspace-error" role="alert">{error}</p>;
  }

  return (
    <section className="workspace-panel">
      <h1>{t("title")}</h1>
      <p className="workspace-description">{t("description")}</p>

      <p className="workspace-actions">
        <Link href="/workspaces/new" className="workspace-button-link">
          {t("createLink")}
        </Link>
      </p>

      {items.length === 0 ? (
        <p className="workspace-empty">{t("empty")}</p>
      ) : (
        <ul className="workspace-list">
          {items.map((item) => (
            <li key={item.workspace.id} className="workspace-list-item">
              <div>
                <h2>{item.workspace.name}</h2>
                <p className="workspace-meta">
                  <span>{item.workspace.slug}</span>
                  <span>
                    {t("roleLabel")}: {item.membership.role}
                  </span>
                  <span>
                    {t("statusLabel")}: {item.workspace.status}
                  </span>
                </p>
              </div>
              <Link href={`/workspaces/${item.workspace.id}`}>
                {t("openLink")}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function WorkspaceList() {
  return (
    <RequireAuth>
      <WorkspaceListContent />
    </RequireAuth>
  );
}
