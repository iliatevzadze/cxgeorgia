"use client";

import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

type LocaleSwitcherProps = {
  languageLabel: string;
};

export function LocaleSwitcher({ languageLabel }: LocaleSwitcherProps) {
  const locale = useLocale();
  const t = useTranslations("locale");

  return (
    <nav className="locale-switcher" aria-label={languageLabel}>
      <span className="locale-switcher-label">{languageLabel}</span>
      <div className="locale-switcher-links">
        <Link
          href="/"
          locale="ka"
          className={`locale-link${locale === "ka" ? " active" : ""}`}
        >
          {t("ka")}
        </Link>
        <Link
          href="/"
          locale="en"
          className={`locale-link${locale === "en" ? " active" : ""}`}
        >
          {t("en")}
        </Link>
      </div>
    </nav>
  );
}
