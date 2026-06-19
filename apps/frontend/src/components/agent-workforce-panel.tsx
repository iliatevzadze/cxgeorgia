"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";
import {
  clockInAgentShift,
  clockOutAgentShift,
  getMyActiveAgentShift,
  listActiveAgentShifts,
  listAgentCaseMetrics,
} from "@/lib/agent-workforce/api";
import type { AgentCaseMetric, AgentShift } from "@/lib/agent-workforce/types";
import { getAccessToken } from "@/lib/auth/token-storage";

type AgentWorkforcePanelProps = {
  workspaceId: string;
};

function formatDateTime(value: string | null, locale: string, noValue: string): string {
  if (!value) {
    return noValue;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function AgentWorkforcePanel({ workspaceId }: AgentWorkforcePanelProps) {
  const t = useTranslations("workspaces.app.workforce");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();

  const [myShift, setMyShift] = useState<AgentShift | null>(null);
  const [activeShifts, setActiveShifts] = useState<AgentShift[]>([]);
  const [caseMetrics, setCaseMetrics] = useState<AgentCaseMetric[]>([]);
  const [filterUserId, setFilterUserId] = useState("");
  const [filterCaseId, setFilterCaseId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isShiftUpdating, setIsShiftUpdating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [shiftErrorMessage, setShiftErrorMessage] = useState<string | null>(null);

  const noValue = t("noValue");

  const loadWorkforceData = useCallback(
    async (filters?: { user_id?: string; case_id?: string }) => {
      const token = getAccessToken();
      if (!token) {
        setErrorMessage(tCommon("accessDenied"));
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setErrorMessage(null);

      try {
        const [shift, shifts, metrics] = await Promise.all([
          getMyActiveAgentShift(workspaceId, token),
          listActiveAgentShifts(workspaceId, token),
          listAgentCaseMetrics(workspaceId, token, filters ?? {}),
        ]);
        setMyShift(shift);
        setActiveShifts(shifts);
        setCaseMetrics(metrics);
      } catch (error) {
        setMyShift(null);
        setActiveShifts([]);
        setCaseMetrics([]);

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
    },
    [workspaceId, t, tCommon],
  );

  useEffect(() => {
    void loadWorkforceData();
  }, [loadWorkforceData]);

  async function refreshShiftData() {
    const token = getAccessToken();
    if (!token) {
      return;
    }

    try {
      const [shift, shifts] = await Promise.all([
        getMyActiveAgentShift(workspaceId, token),
        listActiveAgentShifts(workspaceId, token),
      ]);
      setMyShift(shift);
      setActiveShifts(shifts);
    } catch {
      // Keep panel usable; shift section shows last known state.
    }
  }

  async function handleClockIn() {
    setShiftErrorMessage(null);

    const token = getAccessToken();
    if (!token) {
      setShiftErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsShiftUpdating(true);

    try {
      await clockInAgentShift(workspaceId, token);
      await refreshShiftData();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setShiftErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setShiftErrorMessage(tCommon("accessDenied"));
        } else {
          setShiftErrorMessage(t("shiftUpdateError"));
        }
      } else {
        setShiftErrorMessage(t("shiftUpdateError"));
      }
    } finally {
      setIsShiftUpdating(false);
    }
  }

  async function handleClockOut() {
    setShiftErrorMessage(null);

    const token = getAccessToken();
    if (!token) {
      setShiftErrorMessage(tCommon("accessDenied"));
      return;
    }

    setIsShiftUpdating(true);

    try {
      await clockOutAgentShift(workspaceId, token);
      await refreshShiftData();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setShiftErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setShiftErrorMessage(tCommon("accessDenied"));
        } else {
          setShiftErrorMessage(t("shiftUpdateError"));
        }
      } else {
        setShiftErrorMessage(t("shiftUpdateError"));
      }
    } finally {
      setIsShiftUpdating(false);
    }
  }

  async function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadWorkforceData({
      user_id: filterUserId.trim() || undefined,
      case_id: filterCaseId.trim() || undefined,
    });
  }

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (errorMessage) {
    return (
      <section className="workspace-panel workspace-agent-workforce-panel">
        <p className="workspace-error" role="alert">
          {errorMessage}
        </p>
      </section>
    );
  }

  const hasActiveShift = myShift !== null && myShift.is_active;

  return (
    <div className="workspace-agent-workforce">
      <section className="workspace-panel workspace-agent-workforce-panel">
        <h2>{t("title")}</h2>

        <section className="workspace-agent-workforce-section">
          <h3>{t("myShift")}</h3>

          {shiftErrorMessage ? (
            <p className="workspace-error" role="alert">
              {shiftErrorMessage}
            </p>
          ) : null}

          <dl className="account-details">
            <div>
              <dt>{t("shiftStatusLabel")}</dt>
              <dd>{hasActiveShift ? t("activeShift") : t("noActiveShift")}</dd>
            </div>
            <div>
              <dt>{t("clockInAtLabel")}</dt>
              <dd>
                {formatDateTime(
                  hasActiveShift ? myShift.clock_in_at : null,
                  locale,
                  noValue,
                )}
              </dd>
            </div>
          </dl>

          <div className="workspace-agent-workforce-actions">
            <button
              type="button"
              className="auth-submit"
              disabled={isShiftUpdating || hasActiveShift}
              onClick={() => void handleClockIn()}
            >
              {isShiftUpdating && !hasActiveShift ? t("clockingIn") : t("clockIn")}
            </button>
            <button
              type="button"
              className="workspace-agent-workforce-secondary-button"
              disabled={isShiftUpdating || !hasActiveShift}
              onClick={() => void handleClockOut()}
            >
              {isShiftUpdating && hasActiveShift ? t("clockingOut") : t("clockOut")}
            </button>
          </div>
        </section>

        <section className="workspace-agent-workforce-section">
          <h3>{t("activeShifts")}</h3>
          {activeShifts.length === 0 ? (
            <p className="workspace-empty">{t("noActiveShifts")}</p>
          ) : (
            <ul className="workspace-agent-workforce-list">
              {activeShifts.map((shift) => (
                <li key={shift.id} className="workspace-agent-workforce-item">
                  <dl className="account-details">
                    <div>
                      <dt>{t("userId")}</dt>
                      <dd>{shift.user_id}</dd>
                    </div>
                    <div>
                      <dt>{t("clockInAtLabel")}</dt>
                      <dd>
                        {formatDateTime(shift.clock_in_at, locale, noValue)}
                      </dd>
                    </div>
                  </dl>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="workspace-agent-workforce-section">
          <h3>{t("caseMetrics")}</h3>

          <form
            className="workspace-form workspace-agent-workforce-filters"
            onSubmit={(event) => void handleFilterSubmit(event)}
          >
            <label className="auth-field">
              <span>{t("filterUserId")}</span>
              <input
                type="text"
                name="filterUserId"
                value={filterUserId}
                onChange={(event) => setFilterUserId(event.target.value)}
              />
            </label>
            <label className="auth-field">
              <span>{t("filterCaseId")}</span>
              <input
                type="text"
                name="filterCaseId"
                value={filterCaseId}
                onChange={(event) => setFilterCaseId(event.target.value)}
              />
            </label>
            <button type="submit" className="auth-submit">
              {t("applyFilters")}
            </button>
          </form>

          {caseMetrics.length === 0 ? (
            <p className="workspace-empty">{t("noCaseMetrics")}</p>
          ) : (
            <ul className="workspace-agent-workforce-list">
              {caseMetrics.map((metric) => (
                <li key={metric.id} className="workspace-agent-workforce-item">
                  <dl className="account-details">
                    <div>
                      <dt>{t("userId")}</dt>
                      <dd>{metric.user_id}</dd>
                    </div>
                    <div>
                      <dt>{t("caseId")}</dt>
                      <dd>{metric.case_id}</dd>
                    </div>
                    <div>
                      <dt>{t("assignedAt")}</dt>
                      <dd>
                        {formatDateTime(metric.assigned_at, locale, noValue)}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("firstResponseAt")}</dt>
                      <dd>
                        {formatDateTime(
                          metric.first_response_at,
                          locale,
                          noValue,
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("resolvedAt")}</dt>
                      <dd>
                        {formatDateTime(metric.resolved_at, locale, noValue)}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("messagesCount")}</dt>
                      <dd>{metric.messages_count}</dd>
                    </div>
                  </dl>
                </li>
              ))}
            </ul>
          )}
        </section>
      </section>
    </div>
  );
}
