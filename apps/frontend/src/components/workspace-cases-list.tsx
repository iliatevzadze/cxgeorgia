"use client";

import { useCallback, useEffect, useState } from "react";

import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { WorkspaceCaseCreateForm } from "@/components/workspace-case-create-form";
import { ApiError } from "@/lib/api/errors";
import { listCases } from "@/lib/cases/api";
import type { UniversalCaseRead } from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";
import { workspaceRoutes } from "@/lib/workspaces/routes";

type WorkspaceCasesListProps = {
  workspaceId: string;
};

function formatCreatedAt(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatCustomer(item: UniversalCaseRead, fallback: string): string {
  return item.customer_name ?? item.customer_email ?? fallback;
}

export function WorkspaceCasesList({ workspaceId }: WorkspaceCasesListProps) {
  const t = useTranslations("workspaces.app.cases");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();

  const [cases, setCases] = useState<UniversalCaseRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const loadCases = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setErrorMessage(tCommon("accessDenied"));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const items = await listCases(workspaceId, token);
      setCases(items);
    } catch (error) {
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
      setIsLoading(false);
    }
  }, [workspaceId, t, tCommon]);

  useEffect(() => {
    void loadCases();
  }, [loadCases, refreshToken]);

  function handleCaseCreated() {
    setRefreshToken((current) => current + 1);
  }

  return (
    <div className="workspace-cases-page">
      <WorkspaceCaseCreateForm
        workspaceId={workspaceId}
        onCreated={handleCaseCreated}
      />

      {isLoading ? (
        <p className="workspace-status">{t("loading")}</p>
      ) : errorMessage ? (
        <section className="workspace-panel">
          <p className="workspace-error" role="alert">
            {errorMessage}
          </p>
        </section>
      ) : (
        <section className="workspace-panel">
          <h1>{t("title")}</h1>
          <p className="workspace-description">{t("description")}</p>

          {cases.length === 0 ? (
            <div className="workspace-empty">
              <p>{t("emptyTitle")}</p>
              <p>{t("emptyMessage")}</p>
            </div>
          ) : (
            <ul className="workspace-cases">
              {cases.map((item) => (
                <li key={item.id} className="workspace-case-item">
                  <h2>
                    <Link href={workspaceRoutes.appCaseDetail(workspaceId, item.id)}>
                      {item.title}
                    </Link>
                  </h2>
                  <dl className="account-details">
                    <div>
                      <dt>{t("statusLabel")}</dt>
                      <dd>{item.status}</dd>
                    </div>
                    <div>
                      <dt>{t("priorityLabel")}</dt>
                      <dd>{item.priority}</dd>
                    </div>
                    <div>
                      <dt>{t("sourceLabel")}</dt>
                      <dd>{item.source}</dd>
                    </div>
                    <div>
                      <dt>{t("customerLabel")}</dt>
                      <dd>{formatCustomer(item, t("noCustomer"))}</dd>
                    </div>
                    <div>
                      <dt>{t("createdAtLabel")}</dt>
                      <dd>{formatCreatedAt(item.created_at, locale)}</dd>
                    </div>
                  </dl>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
