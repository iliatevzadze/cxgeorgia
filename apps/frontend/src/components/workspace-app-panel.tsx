"use client";

import { WorkspaceAppHome } from "@/components/workspace-app-home";
import { WorkspaceAppSectionPanel } from "@/components/workspace-app-section-panel";

type WorkspaceAppPanelProps = {
  workspaceId: string;
};

export function WorkspaceAppPanel({ workspaceId }: WorkspaceAppPanelProps) {
  return (
    <WorkspaceAppSectionPanel workspaceId={workspaceId} activeSection="home">
      <WorkspaceAppHome />
    </WorkspaceAppSectionPanel>
  );
}
