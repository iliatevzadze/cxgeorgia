"use client";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { useAuth } from "@/hooks/use-auth";

export function AuthNav() {
  const t = useTranslations("auth.nav");
  const { isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return (
      <nav className="auth-nav" aria-label={t("label")}>
        <Link href="/account">{t("account")}</Link>
        <button type="button" className="link-button" onClick={logout}>
          {t("logout")}
        </button>
      </nav>
    );
  }

  return (
    <nav className="auth-nav" aria-label={t("label")}>
      <Link href="/login">{t("login")}</Link>
      <Link href="/register">{t("register")}</Link>
    </nav>
  );
}
