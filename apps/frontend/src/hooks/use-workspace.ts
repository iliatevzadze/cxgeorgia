"use client";

import { useCallback, useEffect, useState } from "react";

import { useTranslations } from "next-intl";

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

export type UseWorkspaceResult = {
  workspace: WorkspaceRead | null;
  membership: WorkspaceMembershipRead | null;
  isLoading: boolean;
  errorMessage: string | null;
  refresh: () => Promise<void>;
};

export function useWorkspace(workspaceId: string): UseWorkspaceResult {
  const t = useTranslations("workspaces.common");
  const { user } = useAuth();

  const [workspace, setWorkspace] = useState<WorkspaceRead | null>(null);
  const [membership, setMembership] = useState<WorkspaceMembershipRead | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !user) {
      setWorkspace(null);
      setMembership(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [workspaceData, memberships] = await Promise.all([
        getWorkspace(workspaceId, token),
        listWorkspaceMemberships(workspaceId, token),
      ]);

      setWorkspace(workspaceData);
      setMembership(
        memberships.find((item) => item.user_id === user.id) ?? null,
      );
    } catch (error) {
      setWorkspace(null);
      setMembership(null);

      if (error instanceof ApiError) {
        if (error.status === 404) {
          setErrorMessage(t("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setErrorMessage(t("accessDenied"));
        } else {
          setErrorMessage(t("loadError"));
        }
      } else {
        setErrorMessage(t("loadError"));
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, user, t]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    workspace,
    membership,
    isLoading,
    errorMessage,
    refresh,
  };
}
