"use client";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { RequireAuth } from "@/components/require-auth";
import { useAuth } from "@/hooks/use-auth";

function AccountDetails() {
  const t = useTranslations("auth.account");
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <section className="account-panel">
      <h1>{t("title")}</h1>
      <p className="auth-form-description">{t("description")}</p>

      <dl className="account-details">
        <div>
          <dt>{t("emailLabel")}</dt>
          <dd>{user.email}</dd>
        </div>
        <div>
          <dt>{t("fullNameLabel")}</dt>
          <dd>{user.full_name ?? t("noFullName")}</dd>
        </div>
        <div>
          <dt>{t("statusLabel")}</dt>
          <dd>{user.status}</dd>
        </div>
        <div>
          <dt>{t("emailVerifiedLabel")}</dt>
          <dd>{user.is_email_verified ? t("yes") : t("no")}</dd>
        </div>
      </dl>

      <p className="auth-form-footer">
        <Link href="/">{t("backHome")}</Link>
      </p>
    </section>
  );
}

export function AccountPanel() {
  return (
    <RequireAuth>
      <AccountDetails />
    </RequireAuth>
  );
}
