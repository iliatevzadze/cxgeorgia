"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";
import {
  addCaseQaCriteriaScore,
  approveCaseQaReview,
  createCaseQaReview,
  listCaseQaReviews,
  rejectCaseQaReview,
} from "@/lib/cases/qa-api";
import type { CaseQaReview, QaReviewStatus } from "@/lib/cases/qa-types";
import { getAccessToken } from "@/lib/auth/token-storage";
import type { WorkspaceMembershipRead } from "@/lib/workspaces/types";

type CaseQaReviewsProps = {
  workspaceId: string;
  caseId: string;
  memberships: WorkspaceMembershipRead[];
};

type CriteriaFormState = {
  criterionName: string;
  score: string;
  comment: string;
};

const EMPTY_CRITERIA: CriteriaFormState = {
  criterionName: "",
  score: "",
  comment: "",
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

function normalizeOptionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed || null;
}

function formatMemberLabel(membership: WorkspaceMembershipRead): string {
  return `${membership.user_id} (${membership.role})`;
}

export function CaseQaReviews({
  workspaceId,
  caseId,
  memberships,
}: CaseQaReviewsProps) {
  const t = useTranslations("workspaces.app.cases.detail");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();

  const [reviews, setReviews] = useState<CaseQaReview[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [overallComment, setOverallComment] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createValidationError, setCreateValidationError] = useState<
    string | null
  >(null);
  const [criteriaForms, setCriteriaForms] = useState<
    Record<string, CriteriaFormState>
  >({});
  const [addingCriteriaReviewId, setAddingCriteriaReviewId] = useState<
    string | null
  >(null);
  const [criteriaErrorReviewId, setCriteriaErrorReviewId] = useState<
    string | null
  >(null);
  const [criteriaValidationReviewId, setCriteriaValidationReviewId] = useState<
    string | null
  >(null);
  const [criteriaErrorMessage, setCriteriaErrorMessage] = useState<
    string | null
  >(null);
  const [criteriaValidationMessage, setCriteriaValidationMessage] = useState<
    string | null
  >(null);
  const [updatingReviewId, setUpdatingReviewId] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const loadReviews = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setLoadError(tCommon("accessDenied"));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);

    try {
      const items = await listCaseQaReviews(workspaceId, caseId, token);
      setReviews(items);
    } catch (error) {
      setReviews([]);

      if (error instanceof ApiError) {
        if (error.status === 401 || error.status === 403) {
          setLoadError(tCommon("accessDenied"));
        } else if (error.status === 404) {
          setLoadError(tCommon("notFound"));
        } else {
          setLoadError(t("qaReviewsLoadError"));
        }
      } else {
        setLoadError(t("qaReviewsLoadError"));
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, caseId, t, tCommon]);

  useEffect(() => {
    void loadReviews();
  }, [loadReviews]);

  function getCriteriaForm(reviewId: string): CriteriaFormState {
    return criteriaForms[reviewId] ?? EMPTY_CRITERIA;
  }

  function updateCriteriaForm(
    reviewId: string,
    patch: Partial<CriteriaFormState>,
  ) {
    setCriteriaForms((current) => ({
      ...current,
      [reviewId]: {
        ...getCriteriaForm(reviewId),
        ...patch,
      },
    }));
  }

  function statusLabel(status: QaReviewStatus): string {
    return t(`qaStatusOptions.${status}`);
  }

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setCreateValidationError(null);
    setCreateError(null);

    if (!selectedAgentId) {
      setCreateValidationError(t("qaReviewAgentRequired"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setCreateError(tCommon("accessDenied"));
      return;
    }

    setIsCreating(true);

    try {
      const normalizedComment = normalizeOptionalText(overallComment);
      await createCaseQaReview(
        workspaceId,
        caseId,
        {
          reviewed_agent_user_id: selectedAgentId,
          ...(normalizedComment ? { overall_comment: normalizedComment } : {}),
        },
        token,
      );
      setSelectedAgentId("");
      setOverallComment("");
      await loadReviews();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setCreateError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setCreateError(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setCreateValidationError(t("qaReviewValidationError"));
        } else {
          setCreateError(t("qaReviewSaveError"));
        }
      } else {
        setCreateError(t("qaReviewSaveError"));
      }
    } finally {
      setIsCreating(false);
    }
  }

  async function handleCriteriaSubmit(
    event: FormEvent<HTMLFormElement>,
    reviewId: string,
  ) {
    event.preventDefault();

    setCriteriaValidationReviewId(null);
    setCriteriaValidationMessage(null);
    setCriteriaErrorReviewId(null);
    setCriteriaErrorMessage(null);

    const form = getCriteriaForm(reviewId);
    const trimmedName = form.criterionName.trim();
    const trimmedScore = form.score.trim();
    const scoreValue = Number(trimmedScore);

    if (!trimmedName) {
      setCriteriaValidationReviewId(reviewId);
      setCriteriaValidationMessage(t("qaCriterionNameRequired"));
      return;
    }

    if (
      !trimmedScore ||
      !Number.isInteger(scoreValue) ||
      scoreValue < 0 ||
      scoreValue > 100
    ) {
      setCriteriaValidationReviewId(reviewId);
      setCriteriaValidationMessage(t("qaScoreValidationError"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setCriteriaErrorReviewId(reviewId);
      setCriteriaErrorMessage(tCommon("accessDenied"));
      return;
    }

    setAddingCriteriaReviewId(reviewId);

    try {
      const normalizedComment = normalizeOptionalText(form.comment);
      await addCaseQaCriteriaScore(
        workspaceId,
        caseId,
        reviewId,
        {
          criterion_name: trimmedName,
          score: scoreValue,
          ...(normalizedComment ? { comment: normalizedComment } : {}),
        },
        token,
      );
      updateCriteriaForm(reviewId, EMPTY_CRITERIA);
      await loadReviews();
    } catch (error) {
      setCriteriaErrorReviewId(reviewId);

      if (error instanceof ApiError) {
        if (error.status === 404) {
          setCriteriaErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setCriteriaErrorMessage(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setCriteriaValidationReviewId(reviewId);
          setCriteriaValidationMessage(t("qaScoreValidationError"));
        } else {
          setCriteriaErrorMessage(t("qaReviewSaveError"));
        }
      } else {
        setCriteriaErrorMessage(t("qaReviewSaveError"));
      }
    } finally {
      setAddingCriteriaReviewId(null);
    }
  }

  async function handleApprove(reviewId: string) {
    setUpdateError(null);

    const token = getAccessToken();
    if (!token) {
      setUpdateError(tCommon("accessDenied"));
      return;
    }

    setUpdatingReviewId(reviewId);

    try {
      await approveCaseQaReview(workspaceId, caseId, reviewId, token);
      await loadReviews();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setUpdateError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setUpdateError(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setUpdateError(t("qaReviewUpdateError"));
        } else {
          setUpdateError(t("qaReviewUpdateError"));
        }
      } else {
        setUpdateError(t("qaReviewUpdateError"));
      }
    } finally {
      setUpdatingReviewId(null);
    }
  }

  async function handleReject(reviewId: string) {
    setUpdateError(null);

    const token = getAccessToken();
    if (!token) {
      setUpdateError(tCommon("accessDenied"));
      return;
    }

    setUpdatingReviewId(reviewId);

    try {
      await rejectCaseQaReview(workspaceId, caseId, reviewId, token);
      await loadReviews();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setUpdateError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setUpdateError(tCommon("accessDenied"));
        } else if (error.status === 422) {
          setUpdateError(t("qaReviewUpdateError"));
        } else {
          setUpdateError(t("qaReviewUpdateError"));
        }
      } else {
        setUpdateError(t("qaReviewUpdateError"));
      }
    } finally {
      setUpdatingReviewId(null);
    }
  }

  const noValue = t("noValue");
  const isBusy = isCreating || updatingReviewId !== null || addingCriteriaReviewId !== null;

  return (
    <section className="workspace-panel workspace-case-qa-panel">
      <h2>{t("qaReviewsTitle")}</h2>

      {loadError ? (
        <p className="workspace-error" role="alert">
          {loadError}
        </p>
      ) : null}

      {updateError ? (
        <p className="workspace-error" role="alert">
          {updateError}
        </p>
      ) : null}

      {isLoading ? (
        <p className="workspace-status">{t("qaReviewsLoading")}</p>
      ) : (
        <>
          {!loadError && reviews.length === 0 ? (
            <p className="workspace-empty">{t("qaReviewsEmpty")}</p>
          ) : null}

          {!loadError && reviews.length > 0 ? (
            <ul className="workspace-case-qa-reviews">
              {reviews.map((review) => {
                const criteriaForm = getCriteriaForm(review.id);
                const isPending = review.status === "pending";

                return (
                  <li key={review.id} className="workspace-case-qa-review-item">
                    <dl className="account-details">
                      <div>
                        <dt>{t("qaReviewStatusLabel")}</dt>
                        <dd>{statusLabel(review.status)}</dd>
                      </div>
                      <div>
                        <dt>{t("qaScoreLabel")}</dt>
                        <dd>{review.score}</dd>
                      </div>
                      <div>
                        <dt>{t("qaReviewAgentLabel")}</dt>
                        <dd>
                          {review.reviewed_agent_user_id ?? noValue}
                        </dd>
                      </div>
                      <div>
                        <dt>{t("qaReviewerLabel")}</dt>
                        <dd>{review.reviewed_by_user_id ?? noValue}</dd>
                      </div>
                      <div>
                        <dt>{t("qaReviewOverallCommentLabel")}</dt>
                        <dd>{review.overall_comment ?? noValue}</dd>
                      </div>
                      <div>
                        <dt>{t("createdAtLabel")}</dt>
                        <dd>{formatDateTime(review.created_at, locale)}</dd>
                      </div>
                    </dl>

                    {review.criteria_scores.length > 0 ? (
                      <ul className="workspace-case-qa-criteria">
                        {review.criteria_scores.map((criteria) => (
                          <li
                            key={criteria.id}
                            className="workspace-case-qa-criteria-item"
                          >
                            <p>
                              <strong>{criteria.criterion_name}</strong>:{" "}
                              {criteria.score}
                            </p>
                            {criteria.comment ? (
                              <p>{criteria.comment}</p>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    ) : null}

                    {isPending ? (
                      <div className="workspace-case-qa-review-actions">
                        <button
                          type="button"
                          className="auth-submit"
                          disabled={isBusy}
                          onClick={() => void handleApprove(review.id)}
                        >
                          {updatingReviewId === review.id
                            ? t("qaReviewUpdating")
                            : t("qaApproveButton")}
                        </button>
                        <button
                          type="button"
                          className="workspace-case-qa-reject-button"
                          disabled={isBusy}
                          onClick={() => void handleReject(review.id)}
                        >
                          {updatingReviewId === review.id
                            ? t("qaReviewUpdating")
                            : t("qaRejectButton")}
                        </button>
                      </div>
                    ) : null}

                    {isPending ? (
                      <form
                        className="workspace-form workspace-case-qa-criteria-form"
                        onSubmit={(event) =>
                          void handleCriteriaSubmit(event, review.id)
                        }
                      >
                        <h3>{t("qaCriteriaAddTitle")}</h3>

                        {criteriaValidationReviewId === review.id &&
                        criteriaValidationMessage ? (
                          <p className="workspace-error" role="alert">
                            {criteriaValidationMessage}
                          </p>
                        ) : null}

                        {criteriaErrorReviewId === review.id &&
                        criteriaErrorMessage ? (
                          <p className="workspace-error" role="alert">
                            {criteriaErrorMessage}
                          </p>
                        ) : null}

                        <label className="auth-field">
                          <span>{t("qaCriterionNameLabel")}</span>
                          <input
                            type="text"
                            name={`criterionName-${review.id}`}
                            maxLength={128}
                            value={criteriaForm.criterionName}
                            disabled={isBusy}
                            onChange={(event) =>
                              updateCriteriaForm(review.id, {
                                criterionName: event.target.value,
                              })
                            }
                          />
                        </label>

                        <label className="auth-field">
                          <span>{t("qaScoreLabel")}</span>
                          <input
                            type="number"
                            name={`score-${review.id}`}
                            min={0}
                            max={100}
                            value={criteriaForm.score}
                            disabled={isBusy}
                            onChange={(event) =>
                              updateCriteriaForm(review.id, {
                                score: event.target.value,
                              })
                            }
                          />
                        </label>

                        <label className="auth-field">
                          <span>{t("qaCommentLabel")}</span>
                          <textarea
                            name={`comment-${review.id}`}
                            rows={2}
                            value={criteriaForm.comment}
                            disabled={isBusy}
                            onChange={(event) =>
                              updateCriteriaForm(review.id, {
                                comment: event.target.value,
                              })
                            }
                          />
                        </label>

                        <button
                          type="submit"
                          className="auth-submit"
                          disabled={
                            isBusy ||
                            !criteriaForm.criterionName.trim() ||
                            !criteriaForm.score.trim()
                          }
                        >
                          {addingCriteriaReviewId === review.id
                            ? t("qaCriteriaAdding")
                            : t("qaCriteriaAddButton")}
                        </button>
                      </form>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : null}
        </>
      )}

      <form
        className="workspace-form workspace-case-qa-create-form"
        onSubmit={handleCreateSubmit}
      >
        <h3>{t("qaReviewCreateTitle")}</h3>

        {createValidationError ? (
          <p className="workspace-error" role="alert">
            {createValidationError}
          </p>
        ) : null}

        {createError ? (
          <p className="workspace-error" role="alert">
            {createError}
          </p>
        ) : null}

        <label className="auth-field">
          <span>{t("qaReviewAgentLabel")}</span>
          <select
            name="reviewedAgentUserId"
            value={selectedAgentId}
            disabled={isBusy || isLoading || Boolean(loadError)}
            onChange={(event) => setSelectedAgentId(event.target.value)}
          >
            <option value="">{t("qaReviewAgentPlaceholder")}</option>
            {memberships.map((membership) => (
              <option key={membership.id} value={membership.user_id}>
                {formatMemberLabel(membership)}
              </option>
            ))}
          </select>
        </label>

        <label className="auth-field">
          <span>{t("qaReviewOverallCommentLabel")}</span>
          <textarea
            name="overallComment"
            rows={2}
            value={overallComment}
            disabled={isBusy || isLoading || Boolean(loadError)}
            onChange={(event) => setOverallComment(event.target.value)}
          />
        </label>

        <button
          type="submit"
          className="auth-submit"
          disabled={isBusy || isLoading || Boolean(loadError) || !selectedAgentId}
        >
          {isCreating ? t("qaReviewCreating") : t("qaReviewCreateButton")}
        </button>
      </form>
    </section>
  );
}
