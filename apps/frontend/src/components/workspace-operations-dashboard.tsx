"use client";

import { useCallback, useEffect, useState } from "react";

import { useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";
import { getAccessToken } from "@/lib/auth/token-storage";
import { getOperationsDashboard } from "@/lib/operations/api";
import type { OperationsDashboardRead } from "@/lib/operations/types";

type WorkspaceOperationsDashboardProps = {
  workspaceId: string;
};

function formatAverageScore(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }
  return value.toFixed(1);
}

function isDashboardEmpty(data: OperationsDashboardRead): boolean {
  return (
    data.cases.total_cases === 0 &&
    data.agents.active_shifts === 0 &&
    data.agents.total_agent_case_metrics === 0 &&
    data.qa.total_reviews === 0
  );
}

type MetricItemProps = {
  label: string;
  value: number | string;
};

function MetricItem({ label, value }: MetricItemProps) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function WorkspaceOperationsDashboard({
  workspaceId,
}: WorkspaceOperationsDashboardProps) {
  const t = useTranslations("workspaces.app.dashboard");
  const tCommon = useTranslations("workspaces.common");

  const [dashboard, setDashboard] = useState<OperationsDashboardRead | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setErrorMessage(tCommon("accessDenied"));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await getOperationsDashboard(workspaceId, token);
      setDashboard(data);
    } catch (error) {
      setDashboard(null);
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
    void loadDashboard();
  }, [loadDashboard]);

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (errorMessage) {
    return (
      <section className="workspace-panel">
        <p className="workspace-error" role="alert">
          {errorMessage}
        </p>
      </section>
    );
  }

  if (dashboard === null) {
    return null;
  }

  const empty = isDashboardEmpty(dashboard);

  return (
    <div className="workspace-operations-dashboard">
      <section className="workspace-panel">
        <h1>{t("title")}</h1>
        <p className="workspace-description">{t("description")}</p>
        {empty ? (
          <div className="workspace-empty">
            <p>{t("empty")}</p>
          </div>
        ) : null}
      </section>

      <div className="workspace-operations-dashboard-grid">
        <section className="workspace-panel workspace-operations-card">
          <h2>{t("sections.cases")}</h2>
          <dl className="account-details workspace-operations-metrics">
            <MetricItem label={t("metrics.total")} value={dashboard.cases.total_cases} />
            <MetricItem label={t("metrics.open")} value={dashboard.cases.open_cases} />
            <MetricItem
              label={t("metrics.pending")}
              value={dashboard.cases.pending_cases}
            />
            <MetricItem
              label={t("metrics.resolved")}
              value={dashboard.cases.resolved_cases}
            />
          </dl>
        </section>

        <section className="workspace-panel workspace-operations-card">
          <h2>{t("sections.sla")}</h2>
          <dl className="account-details workspace-operations-metrics">
            <MetricItem label={t("metrics.onTrack")} value={dashboard.sla.on_track} />
            <MetricItem label={t("metrics.atRisk")} value={dashboard.sla.at_risk} />
            <MetricItem label={t("metrics.breached")} value={dashboard.sla.breached} />
          </dl>
        </section>

        <section className="workspace-panel workspace-operations-card">
          <h2>{t("sections.agents")}</h2>
          <dl className="account-details workspace-operations-metrics">
            <MetricItem
              label={t("metrics.activeShifts")}
              value={dashboard.agents.active_shifts}
            />
            <MetricItem
              label={t("metrics.agentCaseMetrics")}
              value={dashboard.agents.total_agent_case_metrics}
            />
            <MetricItem
              label={t("metrics.agentMessages")}
              value={dashboard.agents.total_agent_messages}
            />
          </dl>
        </section>

        <section className="workspace-panel workspace-operations-card">
          <h2>{t("sections.qa")}</h2>
          <dl className="account-details workspace-operations-metrics">
            <MetricItem
              label={t("metrics.totalReviews")}
              value={dashboard.qa.total_reviews}
            />
            <MetricItem
              label={t("metrics.pending")}
              value={dashboard.qa.pending_reviews}
            />
            <MetricItem
              label={t("metrics.approved")}
              value={dashboard.qa.approved_reviews}
            />
            <MetricItem
              label={t("metrics.rejected")}
              value={dashboard.qa.rejected_reviews}
            />
            <MetricItem
              label={t("metrics.averageScore")}
              value={formatAverageScore(dashboard.qa.average_score)}
            />
          </dl>
        </section>
      </div>
    </div>
  );
}
