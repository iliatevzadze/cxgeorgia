export type OperationsCasesSummary = {
  total_cases: number;
  open_cases: number;
  pending_cases: number;
  resolved_cases: number;
};

export type OperationsSlaSummary = {
  on_track: number;
  at_risk: number;
  breached: number;
};

export type OperationsAgentsSummary = {
  active_shifts: number;
  total_agent_case_metrics: number;
  total_agent_messages: number;
};

export type OperationsQaSummary = {
  total_reviews: number;
  pending_reviews: number;
  approved_reviews: number;
  rejected_reviews: number;
  average_score: number;
};

export type OperationsDashboardRead = {
  cases: OperationsCasesSummary;
  sla: OperationsSlaSummary;
  agents: OperationsAgentsSummary;
  qa: OperationsQaSummary;
};
