"use client";

import { useState, type FormEvent } from "react";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { RequireAuth } from "@/components/require-auth";
import { useWorkspaces } from "@/hooks/use-workspaces";
import { ApiError } from "@/lib/api/errors";
import type { WorkspaceWithMembershipRead } from "@/lib/workspaces/types";

function WorkspaceCreateFormContent() {
  const t = useTranslations("workspaces.create");
  const { create } = useWorkspaces();

  const [name, setName] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdWorkspace, setCreatedWorkspace] =
    useState<WorkspaceWithMembershipRead | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const workspace = await create(name);
      setCreatedWorkspace(workspace);
      setName("");
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage(t("error"));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (createdWorkspace) {
    return (
      <section className="workspace-panel">
        <h1>{t("title")}</h1>
        <p className="workspace-success" role="status">
          {t("success", { name: createdWorkspace.workspace.name })}
        </p>
        <p className="workspace-actions">
          <Link
            href={`/workspaces/${createdWorkspace.workspace.id}`}
            className="workspace-button-link"
          >
            {t("openWorkspace")}
          </Link>
          <Link href="/workspaces">{t("backToList")}</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="workspace-panel">
      <form className="workspace-form" onSubmit={handleSubmit}>
        <h1>{t("title")}</h1>
        <p className="workspace-description">{t("description")}</p>

        {errorMessage ? (
          <p className="workspace-error" role="alert">
            {errorMessage}
          </p>
        ) : null}

        <label className="auth-field">
          <span>{t("nameLabel")}</span>
          <input
            type="text"
            name="name"
            required
            minLength={2}
            maxLength={120}
            placeholder={t("namePlaceholder")}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>

        <button type="submit" className="auth-submit" disabled={isSubmitting}>
          {isSubmitting ? t("submitting") : t("submit")}
        </button>

        <p className="auth-form-footer">
          <Link href="/workspaces">{t("backToList")}</Link>
        </p>
      </form>
    </section>
  );
}

export function WorkspaceCreateForm() {
  return (
    <RequireAuth>
      <WorkspaceCreateFormContent />
    </RequireAuth>
  );
}
