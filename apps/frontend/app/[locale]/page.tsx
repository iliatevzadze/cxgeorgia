import { getTranslations, setRequestLocale } from "next-intl/server";

import { LocaleSwitcher } from "@/components/locale-switcher";

type HomePageProps = {
  params: Promise<{ locale: string }>;
};

export default async function HomePage({ params }: HomePageProps) {
  const { locale } = await params;

  setRequestLocale(locale);

  const t = await getTranslations("home");

  const notBuiltItems = [
    t("notBuiltAuth"),
    t("notBuiltDashboard"),
    t("notBuiltCases"),
    t("notBuiltIntegrations"),
  ];

  return (
    <main className="page">
      <header className="page-header">
        <span className="phase-badge">{t("phase")}</span>
        <h1>{t("title")}</h1>
        <p className="subtitle">{t("subtitle")}</p>
        <p className="description">{t("description")}</p>
      </header>

      <section className="cards" aria-label={t("statusLabel")}>
        <article className="card">
          <h2>{t("statusLabel")}</h2>
          <p>{t("statusValue")}</p>
        </article>
        <article className="card">
          <h2>{t("backendLabel")}</h2>
          <p>{t("backendValue")}</p>
        </article>
        <article className="card">
          <h2>{t("infrastructureLabel")}</h2>
          <p>{t("infrastructureValue")}</p>
        </article>
      </section>

      <section className="not-built">
        <h2>{t("notBuiltTitle")}</h2>
        <ul>
          {notBuiltItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <footer className="page-footer">
        <LocaleSwitcher languageLabel={t("language")} />
      </footer>
    </main>
  );
}
