"use client";

import { RequireAuth } from "@/components/require-auth";
import { WorkspaceAppHome } from "@/components/workspace-app-home";
import { WorkspaceAppShell } from "@/components/workspace-app-shell";

type WorkspaceAppPanelProps = {
  workspaceId: string;
};

export function WorkspaceAppPanel({ workspaceId }: WorkspaceAppPanelProps) {
  return (
    <RequireAuth>
      <WorkspaceAppShell workspaceId={workspaceId}>
        <WorkspaceAppHome />
      </WorkspaceAppShell>
    </RequireAuth>
  );
}
