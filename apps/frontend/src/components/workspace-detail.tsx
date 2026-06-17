"use client";

import { useEffect, useState } from "react";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { RequireAuth } from "@/components/require-auth";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";
import { getAccessToken } from "@/lib/auth/token-storage";
import {
  getWorkspace,
  listWorkspaceMemberships,
} from "@/lib/workspaces/api";
import type {
  WorkspaceMembershipRead,
  WorkspaceRead,
} from "@/lib/workspaces/types";

type WorkspaceDetailProps = {
  workspaceId: string;
};

function WorkspaceDetailContent({ workspaceId }: WorkspaceDetailProps) {
  const t = useTranslations("workspaces.detail");
  const { user } = useAuth();

  const [workspace, setWorkspace] = useState<WorkspaceRead | null>(null);
  const [membership, setMembership] = useState<WorkspaceMembershipRead | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadWorkspace() {
      const token = getAccessToken();
      if (!token || !user) {
        return;
      }

      setIsLoading(true);
      setErrorMessage(null);

      try {
        const [workspaceData, memberships] = await Promise.all([
          getWorkspace(workspaceId, token),
          listWorkspaceMemberships(workspaceId, token),
        ]);

        if (!isMounted) {
          return;
        }

        setWorkspace(workspaceData);
        setMembership(
          memberships.find((item) => item.user_id === user.id) ?? null,
        );
      } catch (error) {
        if (!isMounted) {
          return;
        }

        if (error instanceof ApiError) {
          setErrorMessage(error.message);
        } else {
          setErrorMessage(t("error"));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadWorkspace();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, user, t]);

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (errorMessage || !workspace) {
    return (
      <section className="workspace-panel">
        <p className="workspace-error" role="alert">
          {errorMessage ?? t("error")}
        </p>
        <p className="auth-form-footer">
          <Link href="/workspaces">{t("backToList")}</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="workspace-panel">
      <h1>{t("title")}</h1>
      <p className="workspace-description">{t("description")}</p>

      <dl className="account-details">
        <div>
          <dt>{t("nameLabel")}</dt>
          <dd>{workspace.name}</dd>
        </div>
        <div>
          <dt>{t("slugLabel")}</dt>
          <dd>{workspace.slug}</dd>
        </div>
        <div>
          <dt>{t("statusLabel")}</dt>
          <dd>{workspace.status}</dd>
        </div>
        <div>
          <dt>{t("roleLabel")}</dt>
          <dd>{membership?.role ?? "—"}</dd>
        </div>
      </dl>

      <p className="workspace-actions">
        <Link href={`/workspaces/${workspace.id}/memberships`}>
          {t("membershipsLink")}
        </Link>
        <Link href="/workspaces">{t("backToList")}</Link>
      </p>
    </section>
  );
}

export function WorkspaceDetail({ workspaceId }: WorkspaceDetailProps) {
  return (
    <RequireAuth>
      <WorkspaceDetailContent workspaceId={workspaceId} />
    </RequireAuth>
  );
}
