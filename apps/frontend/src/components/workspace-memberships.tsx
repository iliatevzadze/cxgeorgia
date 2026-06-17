"use client";

import { useEffect, useState } from "react";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { RequireAuth } from "@/components/require-auth";
import { ApiError } from "@/lib/api/errors";
import { getAccessToken } from "@/lib/auth/token-storage";
import { listWorkspaceMemberships } from "@/lib/workspaces/api";
import type { WorkspaceMembershipRead } from "@/lib/workspaces/types";

type WorkspaceMembershipsProps = {
  workspaceId: string;
};

function WorkspaceMembershipsContent({ workspaceId }: WorkspaceMembershipsProps) {
  const t = useTranslations("workspaces.memberships");

  const [memberships, setMemberships] = useState<WorkspaceMembershipRead[]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadMemberships() {
      const token = getAccessToken();
      if (!token) {
        return;
      }

      setIsLoading(true);
      setErrorMessage(null);

      try {
        const items = await listWorkspaceMemberships(workspaceId, token);
        if (isMounted) {
          setMemberships(items);
        }
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

    void loadMemberships();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, t]);

  if (isLoading) {
    return <p className="workspace-status">{t("loading")}</p>;
  }

  if (errorMessage) {
    return (
      <section className="workspace-panel">
        <p className="workspace-error" role="alert">
          {errorMessage}
        </p>
        <p className="auth-form-footer">
          <Link href={`/workspaces/${workspaceId}`}>
            {t("backToWorkspace")}
          </Link>
        </p>
      </section>
    );
  }

  return (
    <section className="workspace-panel">
      <h1>{t("title")}</h1>
      <p className="workspace-description">{t("description")}</p>

      {memberships.length === 0 ? (
        <p className="workspace-empty">{t("empty")}</p>
      ) : (
        <ul className="workspace-memberships">
          {memberships.map((membership) => (
            <li key={membership.id} className="workspace-membership-item">
              <dl className="account-details">
                <div>
                  <dt>{t("userId")}</dt>
                  <dd>{membership.user_id}</dd>
                </div>
                <div>
                  <dt>{t("role")}</dt>
                  <dd>{membership.role}</dd>
                </div>
                <div>
                  <dt>{t("status")}</dt>
                  <dd>{membership.status}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}

      <p className="auth-form-footer">
        <Link href={`/workspaces/${workspaceId}`}>
          {t("backToWorkspace")}
        </Link>
      </p>
    </section>
  );
}

export function WorkspaceMemberships({ workspaceId }: WorkspaceMembershipsProps) {
  return (
    <RequireAuth>
      <WorkspaceMembershipsContent workspaceId={workspaceId} />
    </RequireAuth>
  );
}
