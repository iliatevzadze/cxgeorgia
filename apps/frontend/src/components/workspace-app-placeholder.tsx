"use client";

import { useTranslations } from "next-intl";

import type { WorkspaceAppPlaceholderSection } from "@/lib/workspaces/app-sections";

type WorkspaceAppPlaceholderProps = {
  section: WorkspaceAppPlaceholderSection;
};

export function WorkspaceAppPlaceholder({ section }: WorkspaceAppPlaceholderProps) {
  const t = useTranslations(`workspaces.app.placeholders.${section}`);

  return (
    <section className="workspace-app-placeholder">
      <h2>{t("title")}</h2>
      <p className="workspace-description">{t("description")}</p>
      <p className="workspace-app-not-implemented" role="status">
        {t("notImplemented")}
      </p>
      <p className="workspace-app-future">{t("future")}</p>
    </section>
  );
}
