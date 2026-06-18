"use client";

import { useEffect, useState, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { Link, useRouter } from "@/i18n/navigation";

import { ApiError } from "@/lib/api/errors";
import {
  createCaseComment,
  deleteCase,
  deleteCaseComment,
  getCase,
  listCaseActivities,
  listCaseComments,
  updateCase,
  updateCaseComment,
} from "@/lib/cases/api";
import { getActivityMetadataSummary } from "@/lib/cases/activity-display";
import type {
  CaseActivityRead,
  CaseCommentRead,
  CaseCommentUpdateRequest,
  CasePriority,
  CaseSource,
  CaseStatus,
  UniversalCaseRead,
  UniversalCaseUpdateRequest,
} from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";
import { listWorkspaceMemberships } from "@/lib/workspaces/api";
import { workspaceRoutes } from "@/lib/workspaces/routes";
import type { WorkspaceMembershipRead } from "@/lib/workspaces/types";

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

function formatMemberLabel(membership: WorkspaceMembershipRead): string {
  return `${membership.user_id} (${membership.role})`;
}

function formatAssignmentDisplay(
  assignedToUserId: string | null,
  memberships: WorkspaceMembershipRead[],
  noValue: string,
): string {
  if (!assignedToUserId) {
    return noValue;
  }

  const member = memberships.find(
    (item) => item.user_id === assignedToUserId,
  );
  return member ? formatMemberLabel(member) : assignedToUserId;
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
  const router = useRouter();

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
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteErrorMessage, setDeleteErrorMessage] = useState<string | null>(
    null,
  );
  const [memberships, setMemberships] = useState<WorkspaceMembershipRead[]>(
    [],
  );
  const [isMembershipsLoading, setIsMembershipsLoading] = useState(true);
  const [membershipsLoadError, setMembershipsLoadError] = useState<string | null>(
    null,
  );
  const [selectedAssigneeId, setSelectedAssigneeId] = useState("");
  const [isAssigning, setIsAssigning] = useState(false);
  const [assignmentValidationError, setAssignmentValidationError] = useState<
    string | null
  >(null);
  const [assignmentErrorMessage, setAssignmentErrorMessage] = useState<
    string | null
  >(null);
  const [assignmentSuccessMessage, setAssignmentSuccessMessage] = useState<
    string | null
  >(null);
  const [comments, setComments] = useState<CaseCommentRead[]>([]);
  const [isCommentsLoading, setIsCommentsLoading] = useState(true);
  const [commentsLoadError, setCommentsLoadError] = useState<string | null>(
    null,
  );
  const [commentBody, setCommentBody] = useState("");
  const [commentIsInternal, setCommentIsInternal] = useState(true);
  const [isCommentSubmitting, setIsCommentSubmitting] = useState(false);
  const [commentValidationError, setCommentValidationError] = useState<
    string | null
  >(null);
  const [commentCreateError, setCommentCreateError] = useState<string | null>(
    null,
  );
  const [commentSuccessMessage, setCommentSuccessMessage] = useState<
    string | null
  >(null);
  const [commentDeleteConfirmId, setCommentDeleteConfirmId] = useState<
    string | null
  >(null);
  const [deletingCommentId, setDeletingCommentId] = useState<string | null>(
    null,
  );
  const [commentDeleteErrorMessage, setCommentDeleteErrorMessage] = useState<
    string | null
  >(null);
  const [editingCommentId, setEditingCommentId] = useState<string | null>(
    null,
  );
  const [editCommentBody, setEditCommentBody] = useState("");
  const [editCommentIsInternal, setEditCommentIsInternal] = useState(true);
  const [isCommentEditSaving, setIsCommentEditSaving] = useState(false);
  const [commentEditValidationError, setCommentEditValidationError] = useState<
    string | null
  >(null);
  const [commentEditErrorMessage, setCommentEditErrorMessage] = useState<
    string | null
  >(null);
  const [commentEditSuccessMessage, setCommentEditSuccessMessage] = useState<
    string | null
  >(null);
  const [activities, setActivities] = useState<CaseActivityRead[]>([]);
  const [isActivitiesLoading, setIsActivitiesLoading] = useState(true);
  const [activitiesLoadError, setActivitiesLoadError] = useState<string | null>(
    null,
  );

  useEffect(() => {
    let isMounted = true;

    async function loadCase() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setErrorMessage(tCommon("accessDenied"));
          setIsLoading(false);
          setIsMembershipsLoading(false);
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
          setSelectedAssigneeId(item.assigned_to_user_id ?? "");
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

    async function loadMemberships() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setIsMembershipsLoading(false);
        }
        return;
      }

      setIsMembershipsLoading(true);
      setMembershipsLoadError(null);

      try {
        const items = await listWorkspaceMemberships(workspaceId, token);
        if (isMounted) {
          setMemberships(items.filter((item) => item.status === "active"));
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }

        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403) {
            setMembershipsLoadError(tCommon("accessDenied"));
          } else if (error.status === 404) {
            setMembershipsLoadError(tCommon("notFound"));
          } else {
            setMembershipsLoadError(t("membershipsLoadError"));
          }
        } else {
          setMembershipsLoadError(t("membershipsLoadError"));
        }
      } finally {
        if (isMounted) {
          setIsMembershipsLoading(false);
        }
      }
    }

    void loadCase();
    void loadMemberships();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, caseId, t, tCommon]);

  useEffect(() => {
    if (!caseItem) {
      return;
    }

    let isMounted = true;

    async function loadComments() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setCommentsLoadError(tCommon("accessDenied"));
          setIsCommentsLoading(false);
        }
        return;
      }

      setIsCommentsLoading(true);
      setCommentsLoadError(null);

      try {
        const items = await listCaseComments(workspaceId, caseId, token);
        if (isMounted) {
          setComments(items);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setComments([]);

        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403) {
            setCommentsLoadError(tCommon("accessDenied"));
          } else if (error.status === 404) {
            setCommentsLoadError(tCommon("notFound"));
          } else {
            setCommentsLoadError(t("commentsLoadError"));
          }
        } else {
          setCommentsLoadError(t("commentsLoadError"));
        }
      } finally {
        if (isMounted) {
          setIsCommentsLoading(false);
        }
      }
    }

    void loadComments();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, caseId, caseItem, t, tCommon]);

  useEffect(() => {
    if (!caseItem) {
      return;
    }

    let isMounted = true;

    async function loadActivities() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setActivitiesLoadError(tCommon("accessDenied"));
          setIsActivitiesLoading(false);
        }
        return;
      }

      setIsActivitiesLoading(true);
      setActivitiesLoadError(null);

      try {
        const items = await listCaseActivities(workspaceId, caseId, token);
        if (isMounted) {
          setActivities(items);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setActivities([]);

        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403) {
            setActivitiesLoadError(tCommon("accessDenied"));
          } else if (error.status === 404) {
            setActivitiesLoadError(tCommon("notFound"));
          } else {
            setActivitiesLoadError(t("activitiesLoadError"));
          }
        } else {
          setActivitiesLoadError(t("activitiesLoadError"));
        }
      } finally {
        if (isMounted) {
          setIsActivitiesLoading(false);
        }
      }
    }

    void loadActivities();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, caseId, caseItem, t, tCommon]);

  async function reloadActivities() {
    const token = getAccessToken();
    if (!token) {
      return;
    }

    try {
      const items = await listCaseActivities(workspaceId, caseId, token);
      setActivities(items);
      setActivitiesLoadError(null);
    } catch {
      // Keep the page usable; timeline errors are shown in the activity panel only.
    }
  }

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
  const normalizedSelectedAssignee = selectedAssigneeId || null;
  const hasAssignmentChanges =
    caseItem !== null &&
    normalizedSelectedAssignee !== caseItem.assigned_to_user_id;

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
      await reloadActivities();
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

  async function handleAssignmentSubmit() {
    if (!caseItem) {
      return;
    }

    setAssignmentValidationError(null);
    setAssignmentErrorMessage(null);
    setAssignmentSuccessMessage(null);

    if (!hasAssignmentChanges) {
      setAssignmentValidationError(t("assignmentNoChanges"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setAssignmentErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsAssigning(true);

    try {
      const updated = await updateCase(
        workspaceId,
        caseId,
        { assigned_to_user_id: normalizedSelectedAssignee },
        token,
      );
      setCaseItem(updated);
      setSelectedAssigneeId(updated.assigned_to_user_id ?? "");
      setAssignmentSuccessMessage(t("assignmentSuccess"));
      await reloadActivities();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setAssignmentErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setAssignmentErrorMessage(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setAssignmentValidationError(t("assignmentValidationError"));
        } else {
          setAssignmentErrorMessage(t("assignmentError"));
        }
      } else {
        setAssignmentErrorMessage(t("assignmentError"));
      }
    } finally {
      setIsAssigning(false);
    }
  }

  async function handleCommentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setCommentValidationError(null);
    setCommentCreateError(null);
    setCommentSuccessMessage(null);
    setCommentEditSuccessMessage(null);

    const trimmedBody = commentBody.trim();
    if (!trimmedBody) {
      setCommentValidationError(t("commentBodyRequired"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setCommentCreateError(tCommon("accessDenied"));
      return;
    }

    setIsCommentSubmitting(true);

    try {
      const created = await createCaseComment(
        workspaceId,
        caseId,
        { body: trimmedBody, is_internal: commentIsInternal },
        token,
      );
      setComments((current) => [...current, created]);
      setCommentBody("");
      setCommentIsInternal(true);
      setCommentSuccessMessage(t("commentCreateSuccess"));
      await reloadActivities();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setCommentCreateError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setCommentCreateError(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setCommentValidationError(t("commentValidationError"));
        } else {
          setCommentCreateError(t("commentCreateError"));
        }
      } else {
        setCommentCreateError(t("commentCreateError"));
      }
    } finally {
      setIsCommentSubmitting(false);
    }
  }

  function handleCommentEditClick(comment: CaseCommentRead) {
    setCommentDeleteConfirmId(null);
    setCommentDeleteErrorMessage(null);
    setCommentEditValidationError(null);
    setCommentEditErrorMessage(null);
    setCommentEditSuccessMessage(null);
    setEditingCommentId(comment.id);
    setEditCommentBody(comment.body);
    setEditCommentIsInternal(comment.is_internal);
  }

  function handleCommentEditCancel() {
    setEditingCommentId(null);
    setEditCommentBody("");
    setEditCommentIsInternal(true);
    setCommentEditValidationError(null);
    setCommentEditErrorMessage(null);
  }

  async function handleCommentEditSubmit(
    event: FormEvent<HTMLFormElement>,
    comment: CaseCommentRead,
  ) {
    event.preventDefault();

    setCommentEditValidationError(null);
    setCommentEditErrorMessage(null);
    setCommentEditSuccessMessage(null);

    const trimmedBody = editCommentBody.trim();
    if (!trimmedBody) {
      setCommentEditValidationError(t("commentBodyRequired"));
      return;
    }

    const payload: CaseCommentUpdateRequest = {};
    if (trimmedBody !== comment.body) {
      payload.body = trimmedBody;
    }
    if (editCommentIsInternal !== comment.is_internal) {
      payload.is_internal = editCommentIsInternal;
    }

    const updatePayload: CaseCommentUpdateRequest =
      Object.keys(payload).length > 0
        ? payload
        : { body: trimmedBody, is_internal: editCommentIsInternal };

    const token = getAccessToken();
    if (!token) {
      setCommentEditErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsCommentEditSaving(true);

    try {
      const updated = await updateCaseComment(
        workspaceId,
        caseId,
        comment.id,
        updatePayload,
        token,
      );
      setComments((current) =>
        current.map((item) => (item.id === comment.id ? updated : item)),
      );
      setEditingCommentId(null);
      setEditCommentBody("");
      setEditCommentIsInternal(true);
      setCommentEditSuccessMessage(t("commentEditSuccess"));
      await reloadActivities();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setCommentEditErrorMessage(t("commentDeleteNotFound"));
        } else if (error.status === 401 || error.status === 403) {
          setCommentEditErrorMessage(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setCommentEditValidationError(t("commentValidationError"));
        } else {
          setCommentEditErrorMessage(t("commentEditError"));
        }
      } else {
        setCommentEditErrorMessage(t("commentEditError"));
      }
    } finally {
      setIsCommentEditSaving(false);
    }
  }

  function handleCommentDeleteClick(commentId: string) {
    setCommentDeleteErrorMessage(null);
    setCommentDeleteConfirmId(commentId);
    setEditingCommentId(null);
    setCommentEditValidationError(null);
    setCommentEditErrorMessage(null);
  }

  function handleCommentDeleteCancel() {
    setCommentDeleteConfirmId(null);
    setCommentDeleteErrorMessage(null);
  }

  async function handleCommentDeleteConfirm(commentId: string) {
    setCommentDeleteErrorMessage(null);

    const token = getAccessToken();
    if (!token) {
      setCommentDeleteErrorMessage(tCommon("accessDenied"));
      return;
    }

    setDeletingCommentId(commentId);

    try {
      const result = await deleteCaseComment(
        workspaceId,
        caseId,
        commentId,
        token,
      );
      if (result.deleted) {
        setComments((current) =>
          current.filter((comment) => comment.id !== commentId),
        );
        setCommentDeleteConfirmId(null);
        await reloadActivities();
        return;
      }
      setCommentDeleteErrorMessage(t("commentDeleteError"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setCommentDeleteErrorMessage(t("commentDeleteNotFound"));
        } else if (error.status === 401 || error.status === 403) {
          setCommentDeleteErrorMessage(tCommon("accessDenied"));
        } else {
          setCommentDeleteErrorMessage(t("commentDeleteError"));
        }
      } else {
        setCommentDeleteErrorMessage(t("commentDeleteError"));
      }
    } finally {
      setDeletingCommentId(null);
    }
  }

  async function handleDeleteConfirm() {
    setDeleteErrorMessage(null);

    const token = getAccessToken();
    if (!token) {
      setDeleteErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsDeleting(true);

    try {
      const result = await deleteCase(workspaceId, caseId, token);
      if (result.deleted) {
        router.push(workspaceRoutes.appCases(workspaceId));
        return;
      }
      setDeleteErrorMessage(t("deleteError"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setDeleteErrorMessage(t("deleteNotFound"));
        } else if (error.status === 401 || error.status === 403) {
          setDeleteErrorMessage(tCommon("accessDenied"));
        } else {
          setDeleteErrorMessage(t("deleteError"));
        }
      } else {
        setDeleteErrorMessage(t("deleteError"));
      }
    } finally {
      setIsDeleting(false);
    }
  }

  function handleDeleteCancel() {
    setShowDeleteConfirm(false);
    setDeleteErrorMessage(null);
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

  function formatActivityMetadataSummary(activity: CaseActivityRead): string | null {
    return getActivityMetadataSummary(activity, {
      unassignedLabel: t("assignmentUnassigned"),
      internalLabel: t("commentVisibilityInternal"),
      publicLabel: t("commentVisibilityPublic"),
      formatEnumValue: (field, value) => {
        const raw = String(value);
        if (field === "status_changed") {
          return t(`statusOptions.${raw as CaseStatus}`);
        }
        if (field === "priority_changed") {
          return t(`priorityOptions.${raw as CasePriority}`);
        }
        return raw;
      },
      formatCreatedField: (key, value) => {
        if (key === "title") {
          return `${t("activityCreatedFieldTitle")}: ${String(value)}`;
        }
        if (key === "status") {
          return `${t("statusLabel")}: ${t(`statusOptions.${String(value) as CaseStatus}`)}`;
        }
        if (key === "priority") {
          return `${t("priorityLabel")}: ${t(`priorityOptions.${String(value) as CasePriority}`)}`;
        }
        if (key === "source") {
          return `${t("sourceLabel")}: ${t(`sourceOptions.${String(value) as CaseSource}`)}`;
        }
        return String(value);
      },
    });
  }

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
        <div>
          <dt>{t("assignedToLabel")}</dt>
          <dd>
            {formatAssignmentDisplay(
              caseItem.assigned_to_user_id,
              memberships,
              noValue,
            )}
          </dd>
        </div>
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

      <section className="workspace-panel workspace-case-assignment-panel">
        <h2>{t("assignmentTitle")}</h2>
        <p className="workspace-description">{t("assignmentDescription")}</p>

        {assignmentValidationError ? (
          <p className="workspace-error" role="alert">
            {assignmentValidationError}
          </p>
        ) : null}

        {assignmentErrorMessage ? (
          <p className="workspace-error" role="alert">
            {assignmentErrorMessage}
          </p>
        ) : null}

        {assignmentSuccessMessage ? (
          <p className="workspace-success" role="status">
            {assignmentSuccessMessage}
          </p>
        ) : null}

        {membershipsLoadError ? (
          <p className="workspace-error" role="alert">
            {membershipsLoadError}
          </p>
        ) : null}

        {isMembershipsLoading ? (
          <p className="workspace-status">{t("assignmentLoading")}</p>
        ) : (
          <>
            {!membershipsLoadError && memberships.length === 0 ? (
              <p className="workspace-empty">{t("assignmentMembersEmpty")}</p>
            ) : null}

            <label className="auth-field">
              <span>{t("assignmentLabel")}</span>
              <select
                name="assignedToUserId"
                value={selectedAssigneeId}
                disabled={
                  isAssigning ||
                  isSubmitting ||
                  isDeleting ||
                  isCommentSubmitting ||
                  deletingCommentId !== null ||
                  editingCommentId !== null ||
                  isCommentEditSaving ||
                  Boolean(membershipsLoadError)
                }
                onChange={(event) => setSelectedAssigneeId(event.target.value)}
              >
                <option value="">{t("assignmentUnassigned")}</option>
                {memberships.map((membership) => (
                  <option key={membership.id} value={membership.user_id}>
                    {formatMemberLabel(membership)}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              className="auth-submit"
              disabled={
                isAssigning ||
                isSubmitting ||
                isDeleting ||
                isCommentSubmitting ||
                deletingCommentId !== null ||
                editingCommentId !== null ||
                isCommentEditSaving ||
                Boolean(membershipsLoadError) ||
                !hasAssignmentChanges
              }
              onClick={() => void handleAssignmentSubmit()}
            >
              {isAssigning ? t("assignmentSaving") : t("assignmentSave")}
            </button>
          </>
        )}
      </section>

      <section className="workspace-panel workspace-case-comments-panel">
        <h2>{t("commentsTitle")}</h2>
        <p className="workspace-description">{t("commentsDescription")}</p>

        {commentsLoadError ? (
          <p className="workspace-error" role="alert">
            {commentsLoadError}
          </p>
        ) : null}

        {commentDeleteErrorMessage ? (
          <p className="workspace-error" role="alert">
            {commentDeleteErrorMessage}
          </p>
        ) : null}

        {commentEditSuccessMessage ? (
          <p className="workspace-success" role="status">
            {commentEditSuccessMessage}
          </p>
        ) : null}

        {isCommentsLoading ? (
          <p className="workspace-status">{t("commentsLoading")}</p>
        ) : (
          <>
            {!commentsLoadError && comments.length === 0 ? (
              <p className="workspace-empty">{t("commentsEmpty")}</p>
            ) : null}

            {!commentsLoadError && comments.length > 0 ? (
              <ul className="workspace-case-comments">
                {comments.map((comment) => (
                  <li key={comment.id} className="workspace-case-comment-item">
                    {editingCommentId === comment.id ? (
                      <form
                        className="workspace-form workspace-case-comment-edit-form"
                        onSubmit={(event) =>
                          void handleCommentEditSubmit(event, comment)
                        }
                      >
                        {commentEditValidationError ? (
                          <p className="workspace-error" role="alert">
                            {commentEditValidationError}
                          </p>
                        ) : null}

                        {commentEditErrorMessage ? (
                          <p className="workspace-error" role="alert">
                            {commentEditErrorMessage}
                          </p>
                        ) : null}

                        <label className="auth-field">
                          <span>{t("commentBodyLabel")}</span>
                          <textarea
                            name={`editCommentBody-${comment.id}`}
                            rows={3}
                            value={editCommentBody}
                            disabled={isCommentEditSaving}
                            onChange={(event) =>
                              setEditCommentBody(event.target.value)
                            }
                          />
                        </label>

                        <label className="auth-field workspace-case-comment-internal">
                          <input
                            type="checkbox"
                            name={`editCommentIsInternal-${comment.id}`}
                            checked={editCommentIsInternal}
                            disabled={isCommentEditSaving}
                            onChange={(event) =>
                              setEditCommentIsInternal(event.target.checked)
                            }
                          />
                          <span>{t("commentInternalLabel")}</span>
                        </label>

                        <div className="workspace-case-comment-edit-actions">
                          <button
                            type="submit"
                            className="auth-submit workspace-case-comment-edit-save"
                            disabled={
                              isCommentEditSaving || !editCommentBody.trim()
                            }
                          >
                            {isCommentEditSaving
                              ? t("commentEditSaving")
                              : t("commentEditSave")}
                          </button>
                          <button
                            type="button"
                            className="workspace-case-comment-edit-cancel"
                            disabled={isCommentEditSaving}
                            onClick={handleCommentEditCancel}
                          >
                            {t("commentCancelEditButton")}
                          </button>
                        </div>
                      </form>
                    ) : (
                      <>
                        <p className="workspace-case-comment-body">
                          {comment.body}
                        </p>
                        <dl className="account-details workspace-case-comment-meta">
                          <div>
                            <dt>{t("commentAuthorLabel")}</dt>
                            <dd>
                              {formatOptional(comment.author_user_id, noValue)}
                            </dd>
                          </div>
                          <div>
                            <dt>{t("commentVisibilityLabel")}</dt>
                            <dd>
                              {comment.is_internal
                                ? t("commentVisibilityInternal")
                                : t("commentVisibilityPublic")}
                            </dd>
                          </div>
                          <div>
                            <dt>{t("createdAtLabel")}</dt>
                            <dd>
                              {formatDateTime(comment.created_at, locale)}
                            </dd>
                          </div>
                        </dl>

                        {commentDeleteConfirmId === comment.id ? (
                          <div className="workspace-case-comment-delete-actions">
                            <button
                              type="button"
                              className="auth-submit workspace-case-comment-delete-confirm"
                              disabled={deletingCommentId === comment.id}
                              onClick={() =>
                                void handleCommentDeleteConfirm(comment.id)
                              }
                            >
                              {deletingCommentId === comment.id
                                ? t("commentDeleting")
                                : t("commentConfirmDeleteButton")}
                            </button>
                            <button
                              type="button"
                              className="workspace-case-comment-delete-cancel"
                              disabled={deletingCommentId === comment.id}
                              onClick={handleCommentDeleteCancel}
                            >
                              {t("commentCancelDeleteButton")}
                            </button>
                          </div>
                        ) : (
                          <div className="workspace-case-comment-item-actions">
                            <button
                              type="button"
                              className="auth-submit workspace-case-comment-edit-trigger"
                              disabled={
                                deletingCommentId !== null ||
                                editingCommentId !== null ||
                                isCommentEditSaving ||
                                isCommentSubmitting ||
                                isSubmitting ||
                                isAssigning ||
                                isDeleting
                              }
                              onClick={() => handleCommentEditClick(comment)}
                            >
                              {t("commentEditButton")}
                            </button>
                            <button
                              type="button"
                              className="auth-submit workspace-case-comment-delete-trigger"
                              disabled={
                                deletingCommentId !== null ||
                                editingCommentId !== null ||
                                isCommentEditSaving ||
                                isCommentSubmitting ||
                                isSubmitting ||
                                isAssigning ||
                                isDeleting
                              }
                              onClick={() =>
                                handleCommentDeleteClick(comment.id)
                              }
                            >
                              {t("commentDeleteButton")}
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </li>
                ))}
              </ul>
            ) : null}
          </>
        )}

        <form
          className="workspace-form workspace-case-comment-form"
          onSubmit={handleCommentSubmit}
        >
          {commentValidationError ? (
            <p className="workspace-error" role="alert">
              {commentValidationError}
            </p>
          ) : null}

          {commentCreateError ? (
            <p className="workspace-error" role="alert">
              {commentCreateError}
            </p>
          ) : null}

          {commentSuccessMessage ? (
            <p className="workspace-success" role="status">
              {commentSuccessMessage}
            </p>
          ) : null}

          <label className="auth-field">
            <span>{t("commentBodyLabel")}</span>
            <textarea
              name="commentBody"
              rows={3}
              value={commentBody}
              disabled={
                isCommentSubmitting ||
                isSubmitting ||
                isAssigning ||
                isDeleting ||
                deletingCommentId !== null ||
                editingCommentId !== null ||
                isCommentEditSaving
              }
              onChange={(event) => setCommentBody(event.target.value)}
            />
          </label>

          <label className="auth-field workspace-case-comment-internal">
            <input
              type="checkbox"
              name="commentIsInternal"
              checked={commentIsInternal}
              disabled={
                isCommentSubmitting ||
                isSubmitting ||
                isAssigning ||
                isDeleting ||
                deletingCommentId !== null ||
                editingCommentId !== null ||
                isCommentEditSaving
              }
              onChange={(event) => setCommentIsInternal(event.target.checked)}
            />
            <span>{t("commentInternalLabel")}</span>
          </label>

          <button
            type="submit"
            className="auth-submit"
            disabled={
              isCommentSubmitting ||
              isSubmitting ||
              isAssigning ||
              isDeleting ||
              deletingCommentId !== null ||
              editingCommentId !== null ||
              isCommentEditSaving ||
              !commentBody.trim()
            }
          >
            {isCommentSubmitting ? t("commentSubmitting") : t("commentSubmit")}
          </button>
        </form>
      </section>

      <section className="workspace-panel workspace-case-activities-panel">
        <h2>{t("activitiesTitle")}</h2>
        <p className="workspace-description">{t("activitiesDescription")}</p>

        {activitiesLoadError ? (
          <p className="workspace-error" role="alert">
            {activitiesLoadError}
          </p>
        ) : null}

        {isActivitiesLoading ? (
          <p className="workspace-status">{t("activitiesLoading")}</p>
        ) : (
          <>
            {!activitiesLoadError && activities.length === 0 ? (
              <p className="workspace-empty">{t("activitiesEmpty")}</p>
            ) : null}

            {!activitiesLoadError && activities.length > 0 ? (
              <ul className="workspace-case-activities">
                {activities.map((activity) => {
                  const metadataSummary = formatActivityMetadataSummary(activity);
                  return (
                    <li key={activity.id} className="workspace-case-activity-item">
                      <p className="workspace-case-activity-label">
                        {t(`activityTypeLabels.${activity.activity_type}`)}
                      </p>
                      {activity.message ? (
                        <p className="workspace-case-activity-message">
                          {activity.message}
                        </p>
                      ) : null}
                      {metadataSummary ? (
                        <p className="workspace-case-activity-meta">
                          {metadataSummary}
                        </p>
                      ) : null}
                      <p className="workspace-case-activity-time">
                        {formatDateTime(activity.created_at, locale)}
                      </p>
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </>
        )}
      </section>

      <section className="workspace-panel workspace-case-delete-panel">
        <h2>{t("deleteTitle")}</h2>
        <p className="workspace-description">{t("deleteWarning")}</p>

        {deleteErrorMessage ? (
          <p className="workspace-error" role="alert">
            {deleteErrorMessage}
          </p>
        ) : null}

        {showDeleteConfirm ? (
          <div className="workspace-case-delete-actions">
            <button
              type="button"
              className="auth-submit workspace-case-delete-confirm"
              disabled={isDeleting}
              onClick={() => void handleDeleteConfirm()}
            >
              {isDeleting ? t("deleting") : t("confirmDeleteButton")}
            </button>
            <button
              type="button"
              className="workspace-case-delete-cancel"
              disabled={isDeleting}
              onClick={handleDeleteCancel}
            >
              {t("cancelDeleteButton")}
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="auth-submit workspace-case-delete-trigger"
            disabled={isDeleting || isSubmitting || isAssigning || isCommentSubmitting || deletingCommentId !== null || editingCommentId !== null || isCommentEditSaving}
            onClick={() => {
              setDeleteErrorMessage(null);
              setShowDeleteConfirm(true);
            }}
          >
            {t("deleteButton")}
          </button>
        )}
      </section>

      <p className="auth-form-footer">
        <Link href={workspaceRoutes.appCases(workspaceId)}>
          {t("backToCases")}
        </Link>
      </p>
    </section>
  );
}
