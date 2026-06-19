export type QaReviewStatus = "pending" | "approved" | "rejected";

export type CaseQaCriteriaScore = {
  id: string;
  qa_review_id: string;
  criterion_name: string;
  score: number;
  comment: string | null;
};

export type CaseQaReview = {
  id: string;
  workspace_id: string;
  case_id: string;
  reviewed_by_user_id: string | null;
  reviewed_agent_user_id: string | null;
  score: number;
  status: QaReviewStatus;
  overall_comment: string | null;
  created_at: string;
  updated_at: string;
  criteria_scores: CaseQaCriteriaScore[];
};

export type CaseQaReviewCreateRequest = {
  reviewed_agent_user_id: string;
  overall_comment?: string | null;
};

export type CaseQaCriteriaScoreCreateRequest = {
  criterion_name: string;
  score: number;
  comment?: string | null;
};
