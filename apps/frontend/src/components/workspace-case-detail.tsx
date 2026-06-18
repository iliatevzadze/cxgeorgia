"use client";

import { useEffect, useState, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { ApiError } from "@/lib/api/errors";
import { getCase, updateCase } from "@/lib/cases/api";
import type {
  CasePriority,
  CaseSource,
  CaseStatus,
  UniversalCaseRead,
  UniversalCaseUpdateRequest,
} from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";
import { workspaceRoutes } from "@/lib/workspaces/routes";

const STATUS_OPTIONS: CaseStatus[] = ["open", "pending", "resolved", "closed"];
const PRIORITY_OPTIONS: CasePriority[] = ["low", "normal", "high", "urgent"];
const SOURCE_OPTIONS: CaseSource[] = [
  "manual",
  "email",
  "chat",
  "phone",
  "web",
  "import",
];

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

function normalizeOptionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed || null;
}

function buildUpdatePayload(
  caseItem: UniversalCaseRead,
  title: string,
  description: string,
  status: CaseStatus,
  priority: CasePriority,
  source: CaseSource,
  customerName: string,
  customerEmail: string,
  externalReference: string,
): UniversalCaseUpdateRequest | null {
  const payload: UniversalCaseUpdateRequest = {};
  const trimmedTitle = title.trim();
  const normalizedDescription = normalizeOptionalText(description);
  const normalizedCustomerName = normalizeOptionalText(customerName);
  const normalizedCustomerEmail = normalizeOptionalText(customerEmail);
  const normalizedExternalReference = normalizeOptionalText(externalReference);

  if (trimmedTitle !== caseItem.title) {
    payload.title = trimmedTitle;
  }

  if (normalizedDescription !== caseItem.description) {
    payload.description = normalizedDescription;
  }

  if (status !== caseItem.status) {
    payload.status = status;
  }

  if (priority !== caseItem.priority) {
    payload.priority = priority;
  }

  if (source !== caseItem.source) {
    payload.source = source;
  }

  if (normalizedCustomerName !== caseItem.customer_name) {
    payload.customer_name = normalizedCustomerName;
  }

  if (normalizedCustomerEmail !== caseItem.customer_email) {
    payload.customer_email = normalizedCustomerEmail;
  }

  if (normalizedExternalReference !== caseItem.external_reference) {
    payload.external_reference = normalizedExternalReference;
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
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<CaseStatus>("open");
  const [priority, setPriority] = useState<CasePriority>("normal");
  const [source, setSource] = useState<CaseSource>("manual");
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [externalReference, setExternalReference] = useState("");
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
          setTitle(item.title);
          setDescription(item.description ?? "");
          setStatus(item.status);
          setPriority(item.priority);
          setSource(item.source);
          setCustomerName(item.customer_name ?? "");
          setCustomerEmail(item.customer_email ?? "");
          setExternalReference(item.external_reference ?? "");
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

  const normalizedDescription = normalizeOptionalText(description);
  const normalizedCustomerName = normalizeOptionalText(customerName);
  const normalizedCustomerEmail = normalizeOptionalText(customerEmail);
  const normalizedExternalReference = normalizeOptionalText(externalReference);
  const hasChanges =
    caseItem !== null &&
    (title.trim() !== caseItem.title ||
      normalizedDescription !== caseItem.description ||
      status !== caseItem.status ||
      priority !== caseItem.priority ||
      source !== caseItem.source ||
      normalizedCustomerName !== caseItem.customer_name ||
      normalizedCustomerEmail !== caseItem.customer_email ||
      normalizedExternalReference !== caseItem.external_reference);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!caseItem) {
      return;
    }

    setValidationError(null);
    setUpdateErrorMessage(null);
    setSuccessMessage(null);

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setValidationError(t("titleRequired"));
      return;
    }

    const payload = buildUpdatePayload(
      caseItem,
      title,
      description,
      status,
      priority,
      source,
      customerName,
      customerEmail,
      externalReference,
    );
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
      setTitle(updated.title);
      setDescription(updated.description ?? "");
      setStatus(updated.status);
      setPriority(updated.priority);
      setSource(updated.source);
      setCustomerName(updated.customer_name ?? "");
      setCustomerEmail(updated.customer_email ?? "");
      setExternalReference(updated.external_reference ?? "");
      setSuccessMessage(t("success"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setUpdateErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setUpdateErrorMessage(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setValidationError(t("validationError"));
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
        <div>
          <dt>{t("descriptionLabel")}</dt>
          <dd>{caseItem.description ?? noValue}</dd>
        </div>
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
          <dd>{t(`sourceOptions.${caseItem.source}`)}</dd>
        </div>
        <div>
          <dt>{t("customerNameLabel")}</dt>
          <dd>{caseItem.customer_name ?? noValue}</dd>
        </div>
        <div>
          <dt>{t("customerEmailLabel")}</dt>
          <dd>{caseItem.customer_email ?? noValue}</dd>
        </div>
        <div>
          <dt>{t("externalReferenceLabel")}</dt>
          <dd>{caseItem.external_reference ?? noValue}</dd>
        </div>
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

      <form
        className="workspace-form workspace-case-update-form"
        onSubmit={handleSubmit}
      >
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
          <span>{t("titleLabel")}</span>
          <input
            type="text"
            name="title"
            required
            maxLength={255}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>

        <label className="auth-field">
          <span>{t("descriptionLabel")}</span>
          <textarea
            name="description"
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>

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

        <label className="auth-field">
          <span>{t("sourceLabel")}</span>
          <select
            name="source"
            value={source}
            onChange={(event) =>
              setSource(event.target.value as CaseSource)
            }
          >
            {SOURCE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {t(`sourceOptions.${option}`)}
              </option>
            ))}
          </select>
        </label>

        <label className="auth-field">
          <span>{t("customerNameLabel")}</span>
          <input
            type="text"
            name="customerName"
            maxLength={255}
            value={customerName}
            onChange={(event) => setCustomerName(event.target.value)}
          />
        </label>

        <label className="auth-field">
          <span>{t("customerEmailLabel")}</span>
          <input
            type="text"
            name="customerEmail"
            maxLength={320}
            value={customerEmail}
            onChange={(event) => setCustomerEmail(event.target.value)}
          />
        </label>

        <label className="auth-field">
          <span>{t("externalReferenceLabel")}</span>
          <input
            type="text"
            name="externalReference"
            maxLength={255}
            value={externalReference}
            onChange={(event) => setExternalReference(event.target.value)}
          />
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
