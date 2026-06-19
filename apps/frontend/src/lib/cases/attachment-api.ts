import { apiRequest } from "@/lib/api/client";
import { apiUrl } from "@/lib/api/config";
import { ApiError, parseApiErrorMessage } from "@/lib/api/errors";
import type { ApiEnvelope } from "@/lib/api/types";

import type {
  CaseAttachment,
  CaseAttachmentDeleteResponse,
} from "./attachment-types";

export const caseAttachmentPaths = {
  list: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/attachments`,
  create: (workspaceId: string, caseId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/attachments`,
  detail: (workspaceId: string, caseId: string, attachmentId: string) =>
    `/api/v1/workspaces/${workspaceId}/cases/${caseId}/attachments/${attachmentId}`,
} as const;

export async function listCaseAttachments(
  workspaceId: string,
  caseId: string,
  token: string,
): Promise<CaseAttachment[]> {
  return apiRequest<CaseAttachment[]>(
    caseAttachmentPaths.list(workspaceId, caseId),
    { token },
  );
}

export async function uploadCaseAttachment(
  workspaceId: string,
  caseId: string,
  file: File,
  token: string,
): Promise<CaseAttachment> {
  const formData = new FormData();
  formData.append("file", file);

  if (file.name) {
    formData.append("file_name", file.name);
  }

  if (file.type) {
    formData.append("content_type", file.type);
  }

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(
    apiUrl(caseAttachmentPaths.create(workspaceId, caseId)),
    {
      method: "POST",
      headers,
      body: formData,
    },
  );

  if (!response.ok) {
    const message = await parseApiErrorMessage(response);
    throw new ApiError(message, response.status);
  }

  const payload = (await response.json()) as ApiEnvelope<CaseAttachment>;
  return payload.data;
}

export async function deleteCaseAttachment(
  workspaceId: string,
  caseId: string,
  attachmentId: string,
  token: string,
): Promise<CaseAttachmentDeleteResponse> {
  return apiRequest<CaseAttachmentDeleteResponse>(
    caseAttachmentPaths.detail(workspaceId, caseId, attachmentId),
    {
      method: "DELETE",
      token,
    },
  );
}
