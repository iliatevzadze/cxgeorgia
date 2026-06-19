export type CaseStatus = "open" | "pending" | "resolved" | "closed";

export type CasePriority = "low" | "normal" | "high" | "urgent";

export type CaseSource =
  | "manual"
  | "email"
  | "chat"
  | "phone"
  | "web"
  | "import";

export type CaseSlaStatus = "on_track" | "at_risk" | "breached";

export type UniversalCaseRead = {
  id: string;
  workspace_id: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  priority: CasePriority;
  source: CaseSource;
  customer_name: string | null;
  customer_email: string | null;
  customer_id: string | null;
  external_reference: string | null;
  created_by_user_id: string | null;
  assigned_to_user_id: string | null;
  first_response_due_at: string | null;
  first_response_at: string | null;
  resolution_due_at: string | null;
  resolved_at: string | null;
  sla_status: CaseSlaStatus | null;
  created_at: string;
  updated_at: string;
};

export type UniversalCaseCreateRequest = {
  title: string;
  description?: string;
  priority?: CasePriority;
  source?: CaseSource;
  customer_name?: string;
  customer_email?: string;
  customer_id?: string | null;
  external_reference?: string;
};

export type UniversalCaseUpdateRequest = {
  title?: string;
  description?: string | null;
  status?: CaseStatus;
  priority?: CasePriority;
  source?: CaseSource;
  customer_name?: string | null;
  customer_email?: string | null;
  customer_id?: string | null;
  external_reference?: string | null;
  assigned_to_user_id?: string | null;
};

export type UniversalCaseDeleteResponse = {
  id: string;
  deleted: boolean;
};

export type CaseCommentRead = {
  id: string;
  workspace_id: string;
  case_id: string;
  author_user_id: string | null;
  body: string;
  is_internal: boolean;
  created_at: string;
  updated_at: string;
};

export type CaseCommentCreateRequest = {
  body: string;
  is_internal?: boolean;
};

export type CaseCommentUpdateRequest = {
  body?: string;
  is_internal?: boolean;
};

export type CaseCommentDeleteResponse = {
  id: string;
  deleted: boolean;
};

export type CaseTag = {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  color: string | null;
  created_at: string;
  updated_at: string;
};

export type CaseTagCreateInput = {
  name: string;
  slug: string;
  color?: string;
};

export type CaseTagDetachResponse = {
  tag_id: string;
  detached: boolean;
};

export type CaseActivityType =
  | "case_created"
  | "case_updated"
  | "status_changed"
  | "priority_changed"
  | "assignment_changed"
  | "comment_created"
  | "comment_deleted"
  | "tag_attached"
  | "tag_detached";

export type CaseActivityRead = {
  id: string;
  workspace_id: string;
  case_id: string;
  actor_user_id: string | null;
  activity_type: CaseActivityType;
  message: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type CaseListFilters = {
  status?: CaseStatus;
  priority?: CasePriority;
  source?: CaseSource;
  assigned_to_user_id?: string;
  customer_id?: string;
  sla_status?: CaseSlaStatus;
};
