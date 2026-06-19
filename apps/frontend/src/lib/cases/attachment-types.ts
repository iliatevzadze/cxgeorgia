export type CaseAttachment = {
  id: string;
  workspace_id: string;
  case_id: string;
  uploaded_by_user_id: string | null;
  file_name: string;
  content_type: string | null;
  size_bytes: number;
  storage_bucket: string;
  storage_key: string;
  checksum_sha256: string | null;
  created_at: string;
};

export type CaseAttachmentDeleteResponse = {
  id: string;
  deleted: boolean;
};
