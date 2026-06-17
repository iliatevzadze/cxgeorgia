"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/errors";
import { createWorkspace, listWorkspaces } from "@/lib/workspaces/api";
import { getAccessToken } from "@/lib/auth/token-storage";
import type { WorkspaceWithMembershipRead } from "@/lib/workspaces/types";

export function useWorkspaces() {
  const [items, setItems] = useState<WorkspaceWithMembershipRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setItems([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const workspaces = await listWorkspaces(token);
      setItems(workspaces);
    } catch (loadError) {
      if (loadError instanceof ApiError) {
        setError(loadError.message);
      } else {
        setError("Failed to load workspaces");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const create = useCallback(
    async (name: string) => {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Not authenticated");
      }

      const created = await createWorkspace({ name }, token);
      await refresh();
      return created;
    },
    [refresh],
  );

  return {
    items,
    isLoading,
    error,
    refresh,
    create,
  };
}
