"use client";

import { useEffect, useState } from "react";

import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { ApiError } from "@/lib/api/errors";
import { getCase } from "@/lib/cases/api";
import type { UniversalCaseRead } from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";
import { workspaceRoutes } from "@/lib/workspaces/routes";

type WorkspaceCaseDetailProps = {
  workspaceId: string;
  caseId: string;
};

function formatDateTime(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatOptional(value: string | null, fallback: string): string {
  return value ?? fallback;
}

export function WorkspaceCaseDetail({
  workspaceId,
  caseId,
}: WorkspaceCaseDetailProps) {
  const t = useTranslations("workspaces.app.cases.detail");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();

  const [caseItem, setCaseItem] = useState<UniversalCaseRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadCase() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setErrorMessage(tCommon("accessDenied"));
          setIsLoading(false);
        }
        return;
      }

      setIsLoading(true);
      setErrorMessage(null);

      try {
        const item = await getCase(workspaceId, caseId, token);
        if (isMounted) {
          setCaseItem(item);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setCaseItem(null);

        if (error instanceof ApiError) {
          if (error.status === 404) {
            setErrorMessage(tCommon("notFound"));
          } else if (error.status === 401 || error.status === 403) {
            setErrorMessage(tCommon("accessDenied"));
          } else {
            setErrorMessage(t("error"));
          }
        } else {
          setErrorMessage(t("error"));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadCase();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, caseId, t, tCommon]);

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (errorMessage || !caseItem) {
    return (
      <section className="workspace-panel">
        <p className="workspace-error" role="alert">
          {errorMessage ?? tCommon("notFound")}
        </p>
        <p className="auth-form-footer">
          <Link href={workspaceRoutes.appCases(workspaceId)}>
            {t("backToCases")}
          </Link>
        </p>
      </section>
    );
  }

  const noValue = t("noValue");

  return (
    <section className="workspace-panel">
      <h1>{caseItem.title}</h1>
      <p className="workspace-description">{t("description")}</p>

      <dl className="account-details">
        {caseItem.description ? (
          <div>
            <dt>{t("descriptionLabel")}</dt>
            <dd>{caseItem.description}</dd>
          </div>
        ) : null}
        <div>
          <dt>{t("statusLabel")}</dt>
          <dd>{caseItem.status}</dd>
        </div>
        <div>
          <dt>{t("priorityLabel")}</dt>
          <dd>{caseItem.priority}</dd>
        </div>
        <div>
          <dt>{t("sourceLabel")}</dt>
          <dd>{caseItem.source}</dd>
        </div>
        {caseItem.customer_name ? (
          <div>
            <dt>{t("customerNameLabel")}</dt>
            <dd>{caseItem.customer_name}</dd>
          </div>
        ) : null}
        {caseItem.customer_email ? (
          <div>
            <dt>{t("customerEmailLabel")}</dt>
            <dd>{caseItem.customer_email}</dd>
          </div>
        ) : null}
        {caseItem.external_reference ? (
          <div>
            <dt>{t("externalReferenceLabel")}</dt>
            <dd>{caseItem.external_reference}</dd>
          </div>
        ) : null}
        <div>
          <dt>{t("createdByLabel")}</dt>
          <dd>{formatOptional(caseItem.created_by_user_id, noValue)}</dd>
        </div>
        {caseItem.assigned_to_user_id ? (
          <div>
            <dt>{t("assignedToLabel")}</dt>
            <dd>{caseItem.assigned_to_user_id}</dd>
          </div>
        ) : null}
        <div>
          <dt>{t("createdAtLabel")}</dt>
          <dd>{formatDateTime(caseItem.created_at, locale)}</dd>
        </div>
        <div>
          <dt>{t("updatedAtLabel")}</dt>
          <dd>{formatDateTime(caseItem.updated_at, locale)}</dd>
        </div>
      </dl>

      <p className="auth-form-footer">
        <Link href={workspaceRoutes.appCases(workspaceId)}>
          {t("backToCases")}
        </Link>
      </p>
    </section>
  );
}
