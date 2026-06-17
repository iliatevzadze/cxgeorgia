"use client";

import type { ReactNode } from "react";

import { RequireAuth } from "@/components/require-auth";
import { WorkspaceAppShell } from "@/components/workspace-app-shell";
import type { WorkspaceAppSection } from "@/lib/workspaces/app-sections";

type WorkspaceAppSectionPanelProps = {
  workspaceId: string;
  activeSection: WorkspaceAppSection;
  children: ReactNode;
};

export function WorkspaceAppSectionPanel({
  workspaceId,
  activeSection,
  children,
}: WorkspaceAppSectionPanelProps) {
  return (
    <RequireAuth>
      <WorkspaceAppShell
        workspaceId={workspaceId}
        activeSection={activeSection}
      >
        {children}
      </WorkspaceAppShell>
    </RequireAuth>
  );
}
