"use client";

import { useState, type FormEvent } from "react";

import { useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";
import { createCase } from "@/lib/cases/api";
import type { CasePriority, CaseSource } from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";

const PRIORITY_OPTIONS: CasePriority[] = ["low", "normal", "high", "urgent"];
const SOURCE_OPTIONS: CaseSource[] = [
  "manual",
  "email",
  "chat",
  "phone",
  "web",
  "import",
];

type WorkspaceCaseCreateFormProps = {
  workspaceId: string;
  onCreated?: () => void;
};

function trimOptional(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed || undefined;
}

const defaultFormState = {
  title: "",
  description: "",
  priority: "normal" as CasePriority,
  source: "manual" as CaseSource,
  customerName: "",
  customerEmail: "",
  externalReference: "",
};

export function WorkspaceCaseCreateForm({
  workspaceId,
  onCreated,
}: WorkspaceCaseCreateFormProps) {
  const t = useTranslations("workspaces.app.cases.create");
  const tCommon = useTranslations("workspaces.common");

  const [form, setForm] = useState(defaultFormState);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);
    setErrorMessage(null);
    setSuccessMessage(null);

    const title = form.title.trim();
    if (!title) {
      setValidationError(t("titleRequired"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsSubmitting(true);

    try {
      await createCase(
        workspaceId,
        {
          title,
          description: trimOptional(form.description),
          priority: form.priority,
          source: form.source,
          customer_name: trimOptional(form.customerName),
          customer_email: trimOptional(form.customerEmail),
          external_reference: trimOptional(form.externalReference),
        },
        token,
      );
      setForm(defaultFormState);
      setSuccessMessage(t("success"));
      onCreated?.();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setErrorMessage(tCommon("accessDenied"));
        } else {
          setErrorMessage(error.message || t("error"));
        }
      } else {
        setErrorMessage(t("error"));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="workspace-panel workspace-case-create-panel">
      <form className="workspace-form" onSubmit={handleSubmit}>
        <h2>{t("title")}</h2>
        <p className="workspace-description">{t("description")}</p>

        {validationError ? (
          <p className="workspace-error" role="alert">
            {validationError}
          </p>
        ) : null}

        {errorMessage ? (
          <p className="workspace-error" role="alert">
            {errorMessage}
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
            placeholder={t("titlePlaceholder")}
            value={form.title}
            onChange={(event) =>
              setForm((current) => ({ ...current, title: event.target.value }))
            }
          />
        </label>

        <label className="auth-field">
          <span>{t("descriptionLabel")}</span>
          <textarea
            name="description"
            rows={3}
            value={form.description}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                description: event.target.value,
              }))
            }
          />
        </label>

        <label className="auth-field">
          <span>{t("priorityLabel")}</span>
          <select
            name="priority"
            value={form.priority}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                priority: event.target.value as CasePriority,
              }))
            }
          >
            {PRIORITY_OPTIONS.map((priority) => (
              <option key={priority} value={priority}>
                {t(`priorityOptions.${priority}`)}
              </option>
            ))}
          </select>
        </label>

        <label className="auth-field">
          <span>{t("sourceLabel")}</span>
          <select
            name="source"
            value={form.source}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                source: event.target.value as CaseSource,
              }))
            }
          >
            {SOURCE_OPTIONS.map((source) => (
              <option key={source} value={source}>
                {t(`sourceOptions.${source}`)}
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
            value={form.customerName}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                customerName: event.target.value,
              }))
            }
          />
        </label>

        <label className="auth-field">
          <span>{t("customerEmailLabel")}</span>
          <input
            type="email"
            name="customerEmail"
            maxLength={320}
            value={form.customerEmail}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                customerEmail: event.target.value,
              }))
            }
          />
        </label>

        <label className="auth-field">
          <span>{t("externalReferenceLabel")}</span>
          <input
            type="text"
            name="externalReference"
            maxLength={255}
            value={form.externalReference}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                externalReference: event.target.value,
              }))
            }
          />
        </label>

        <button type="submit" className="auth-submit" disabled={isSubmitting}>
          {isSubmitting ? t("submitting") : t("submit")}
        </button>
      </form>
    </section>
  );
}
