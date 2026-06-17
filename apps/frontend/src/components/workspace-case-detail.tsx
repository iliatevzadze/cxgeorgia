"use client";

import { useEffect, useState, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { ApiError } from "@/lib/api/errors";
import { getCase, updateCase } from "@/lib/cases/api";
import type {
  CasePriority,
  CaseStatus,
  UniversalCaseRead,
  UniversalCaseUpdateRequest,
} from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";
import { workspaceRoutes } from "@/lib/workspaces/routes";

const STATUS_OPTIONS: CaseStatus[] = ["open", "pending", "resolved", "closed"];
const PRIORITY_OPTIONS: CasePriority[] = ["low", "normal", "high", "urgent"];

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

function buildUpdatePayload(
  caseItem: UniversalCaseRead,
  status: CaseStatus,
  priority: CasePriority,
): UniversalCaseUpdateRequest | null {
  const payload: UniversalCaseUpdateRequest = {};

  if (status !== caseItem.status) {
    payload.status = status;
  }

  if (priority !== caseItem.priority) {
    payload.priority = priority;
  }

  return Object.keys(payload).length > 0 ? payload : null;
}

export function WorkspaceCaseDetail({
  workspaceId,
  caseId,
}: WorkspaceCaseDetailProps) {
  const t = useTranslations("workspaces.app.cases.detail");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();

  const [caseItem, setCaseItem] = useState<UniversalCaseRead | null>(null);
  const [status, setStatus] = useState<CaseStatus>("open");
  const [priority, setPriority] = useState<CasePriority>("normal");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [updateErrorMessage, setUpdateErrorMessage] = useState<string | null>(
    null,
  );
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
          setStatus(item.status);
          setPriority(item.priority);
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

  const hasChanges =
    caseItem !== null &&
    (status !== caseItem.status || priority !== caseItem.priority);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!caseItem) {
      return;
    }

    setValidationError(null);
    setUpdateErrorMessage(null);
    setSuccessMessage(null);

    const payload = buildUpdatePayload(caseItem, status, priority);
    if (!payload) {
      setValidationError(t("noChanges"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setUpdateErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsSubmitting(true);

    try {
      const updated = await updateCase(workspaceId, caseId, payload, token);
      setCaseItem(updated);
      setStatus(updated.status);
      setPriority(updated.priority);
      setSuccessMessage(t("success"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setUpdateErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setUpdateErrorMessage(tCommon("accessDenied"));
        } else {
          setUpdateErrorMessage(t("updateError"));
        }
      } else {
        setUpdateErrorMessage(t("updateError"));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

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
          <dd>{t(`statusOptions.${caseItem.status}`)}</dd>
        </div>
        <div>
          <dt>{t("priorityLabel")}</dt>
          <dd>{t(`priorityOptions.${caseItem.priority}`)}</dd>
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

      <form className="workspace-form workspace-case-update-form" onSubmit={handleSubmit}>
        <h2>{t("updateTitle")}</h2>
        <p className="workspace-description">{t("updateDescription")}</p>

        {validationError ? (
          <p className="workspace-error" role="alert">
            {validationError}
          </p>
        ) : null}

        {updateErrorMessage ? (
          <p className="workspace-error" role="alert">
            {updateErrorMessage}
          </p>
        ) : null}

        {successMessage ? (
          <p className="workspace-success" role="status">
            {successMessage}
          </p>
        ) : null}

        <label className="auth-field">
          <span>{t("statusLabel")}</span>
          <select
            name="status"
            value={status}
            onChange={(event) =>
              setStatus(event.target.value as CaseStatus)
            }
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {t(`statusOptions.${option}`)}
              </option>
            ))}
          </select>
        </label>

        <label className="auth-field">
          <span>{t("priorityLabel")}</span>
          <select
            name="priority"
            value={priority}
            onChange={(event) =>
              setPriority(event.target.value as CasePriority)
            }
          >
            {PRIORITY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {t(`priorityOptions.${option}`)}
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          className="auth-submit"
          disabled={isSubmitting || !hasChanges}
        >
          {isSubmitting ? t("submitting") : t("submit")}
        </button>
      </form>

      <p className="auth-form-footer">
        <Link href={workspaceRoutes.appCases(workspaceId)}>
          {t("backToCases")}
        </Link>
      </p>
    </section>
  );
}
