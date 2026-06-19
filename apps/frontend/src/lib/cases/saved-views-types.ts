import type {
  CaseListSortBy,
  CaseListSortOrder,
  CasePriority,
  CaseSlaStatus,
  CaseSource,
  CaseStatus,
} from "./types";

export type CaseListViewPageSize = 10 | 25 | 50 | 100;

export type CaseListViewFilters = {
  status?: CaseStatus;
  priority?: CasePriority;
  source?: CaseSource;
  sla_status?: CaseSlaStatus;
  customer_id?: string;
  assigned_to_user_id?: string;
};

export type CaseListViewRead = {
  id: string;
  workspace_id: string;
  created_by_user_id: string | null;
  name: string;
  description: string | null;
  filters: CaseListViewFilters;
  sort_by: CaseListSortBy | null;
  sort_order: CaseListSortOrder | null;
  page_size: CaseListViewPageSize | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type CaseListViewCreateRequest = {
  name: string;
  description?: string | null;
  filters?: CaseListViewFilters;
  sort_by?: CaseListSortBy;
  sort_order?: CaseListSortOrder;
  page_size?: CaseListViewPageSize;
  is_default?: boolean;
};

export type CaseListViewUpdateRequest = {
  name?: string;
  description?: string | null;
  filters?: CaseListViewFilters;
  sort_by?: CaseListSortBy | null;
  sort_order?: CaseListSortOrder | null;
  page_size?: CaseListViewPageSize | null;
  is_default?: boolean;
};

export type CaseListViewDeleteResponse = {
  id: string;
  deleted: boolean;
};
