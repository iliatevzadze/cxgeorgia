"use client";

import { useTranslations } from "next-intl";

export function WorkspaceAppHome() {
  const t = useTranslations("workspaces.app.home");

  const notBuiltItems = [
    t("notBuiltDashboard"),
    t("notBuiltCases"),
    t("notBuiltCustomers"),
    t("notBuiltIntegrations"),
  ];

  return (
    <section className="workspace-app-home">
      <h2>{t("title")}</h2>
      <p className="workspace-description">{t("description")}</p>
      <p className="workspace-app-ready">{t("ready")}</p>

      <h3>{t("notBuiltTitle")}</h3>
      <ul className="workspace-app-not-built">
        {notBuiltItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
