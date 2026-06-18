export type CaseStatus = "open" | "pending" | "resolved" | "closed";

export type CasePriority = "low" | "normal" | "high" | "urgent";

export type CaseSource =
  | "manual"
  | "email"
  | "chat"
  | "phone"
  | "web"
  | "import";

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
  external_reference: string | null;
  created_by_user_id: string | null;
  assigned_to_user_id: string | null;
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
  external_reference?: string | null;
};

export type UniversalCaseDeleteResponse = {
  id: string;
  deleted: boolean;
};
