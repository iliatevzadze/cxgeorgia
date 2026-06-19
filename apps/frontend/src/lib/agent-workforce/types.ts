export type AgentShift = {
  id: string;
  workspace_id: string;
  user_id: string;
  clock_in_at: string;
  clock_out_at: string | null;
  is_active: boolean;
  created_at: string;
};

export type AgentCaseMetric = {
  id: string;
  workspace_id: string;
  case_id: string;
  user_id: string;
  assigned_at: string | null;
  first_response_at: string | null;
  resolved_at: string | null;
  messages_count: number;
};

export type CaseMetricsFilters = {
  user_id?: string;
  case_id?: string;
};
