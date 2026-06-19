"use client";

import { useCallback, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";
import {
  deleteCaseAttachment,
  listCaseAttachments,
  uploadCaseAttachment,
} from "@/lib/cases/attachment-api";
import type { CaseAttachment } from "@/lib/cases/attachment-types";
import { getAccessToken } from "@/lib/auth/token-storage";

type CaseAttachmentsProps = {
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

function formatFileSize(bytes: number, locale: string): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toLocaleString(locale, { maximumFractionDigits: 1 })} ${units[unitIndex]}`;
}

export function CaseAttachments({ workspaceId, caseId }: CaseAttachmentsProps) {
  const t = useTranslations("workspaces.app.cases.detail");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [attachments, setAttachments] = useState<CaseAttachment[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingAttachmentId, setDeletingAttachmentId] = useState<string | null>(
    null,
  );
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const noValue = t("noValue");

  const loadAttachments = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setLoadError(tCommon("accessDenied"));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);

    try {
      const items = await listCaseAttachments(workspaceId, caseId, token);
      setAttachments(items);
    } catch (error) {
      setAttachments([]);

      if (error instanceof ApiError) {
        if (error.status === 404) {
          setLoadError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setLoadError(tCommon("accessDenied"));
        } else {
          setLoadError(t("attachmentsLoadError"));
        }
      } else {
        setLoadError(t("attachmentsLoadError"));
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, caseId, t, tCommon]);

  useEffect(() => {
    void loadAttachments();
  }, [loadAttachments]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadError(null);
  }

  async function handleUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploadError(null);

    if (!selectedFile) {
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setUploadError(tCommon("accessDenied"));
      return;
    }

    setIsUploading(true);

    try {
      await uploadCaseAttachment(workspaceId, caseId, selectedFile, token);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await loadAttachments();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setUploadError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setUploadError(tCommon("accessDenied"));
        } else {
          setUploadError(t("attachmentUploadError"));
        }
      } else {
        setUploadError(t("attachmentUploadError"));
      }
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(attachmentId: string) {
    setDeleteError(null);

    const token = getAccessToken();
    if (!token) {
      setDeleteError(tCommon("accessDenied"));
      return;
    }

    setDeletingAttachmentId(attachmentId);

    try {
      await deleteCaseAttachment(workspaceId, caseId, attachmentId, token);
      await loadAttachments();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setDeleteError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setDeleteError(tCommon("accessDenied"));
        } else {
          setDeleteError(t("attachmentDeleteError"));
        }
      } else {
        setDeleteError(t("attachmentDeleteError"));
      }
    } finally {
      setDeletingAttachmentId(null);
    }
  }

  const isBusy = isUploading || deletingAttachmentId !== null;

  return (
    <section className="workspace-panel workspace-case-attachments-panel">
      <h2>{t("attachmentsTitle")}</h2>

      {loadError ? (
        <p className="workspace-error" role="alert">
          {loadError}
        </p>
      ) : null}

      {deleteError ? (
        <p className="workspace-error" role="alert">
          {deleteError}
        </p>
      ) : null}

      {isLoading ? (
        <p className="workspace-status">{t("attachmentsLoading")}</p>
      ) : (
        <>
          {!loadError && attachments.length === 0 ? (
            <p className="workspace-empty">{t("attachmentsEmpty")}</p>
          ) : null}

          {attachments.length > 0 ? (
            <ul className="workspace-case-attachments">
              {attachments.map((attachment) => (
                <li
                  key={attachment.id}
                  className="workspace-case-attachment-item"
                >
                  <dl className="account-details">
                    <div>
                      <dt>{t("attachmentFileName")}</dt>
                      <dd>{attachment.file_name}</dd>
                    </div>
                    <div>
                      <dt>{t("attachmentContentType")}</dt>
                      <dd>{attachment.content_type ?? noValue}</dd>
                    </div>
                    <div>
                      <dt>{t("attachmentFileSize")}</dt>
                      <dd>
                        {formatFileSize(attachment.size_bytes, locale)}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("attachmentUploadedAt")}</dt>
                      <dd>
                        {formatDateTime(attachment.created_at, locale)}
                      </dd>
                    </div>
                  </dl>
                  <button
                    type="button"
                    className="workspace-case-attachment-delete"
                    disabled={isBusy}
                    onClick={() => void handleDelete(attachment.id)}
                  >
                    {deletingAttachmentId === attachment.id
                      ? t("attachmentDeleting")
                      : t("attachmentDeleteButton")}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </>
      )}

      <form
        className="workspace-form workspace-case-attachment-upload-form"
        onSubmit={(event) => void handleUploadSubmit(event)}
      >
        <h3>{t("attachmentUploadTitle")}</h3>

        {uploadError ? (
          <p className="workspace-error" role="alert">
            {uploadError}
          </p>
        ) : null}

        <label className="auth-field">
          <span>{t("attachmentChooseFile")}</span>
          <input
            ref={fileInputRef}
            type="file"
            name="attachmentFile"
            disabled={isBusy || isLoading}
            onChange={handleFileChange}
          />
        </label>

        {selectedFile ? (
          <p className="workspace-case-attachment-selected">
            {t("attachmentSelectedFile")}: {selectedFile.name}
          </p>
        ) : null}

        <button
          type="submit"
          className="auth-submit"
          disabled={isBusy || isLoading || !selectedFile}
        >
          {isUploading ? t("attachmentUploading") : t("attachmentUploadButton")}
        </button>
      </form>
    </section>
  );
}
