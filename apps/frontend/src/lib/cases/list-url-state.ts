import type {
  CasePriority,
  CaseSlaStatus,
  CaseSource,
  CaseStatus,
} from "./types";

export type CaseListFilterState = {
  status: CaseStatus | "";
  priority: CasePriority | "";
  source: CaseSource | "";
  sla_status: CaseSlaStatus | "";
  customer_id: string;
  assigned_to_user_id: string;
};

export const EMPTY_CASE_LIST_FILTERS: CaseListFilterState = {
  status: "",
  priority: "",
  source: "",
  sla_status: "",
  customer_id: "",
  assigned_to_user_id: "",
};

export const CASE_LIST_FILTER_QUERY_KEYS = [
  "status",
  "priority",
  "source",
  "sla_status",
  "customer_id",
  "assigned_to_user_id",
] as const;

export const CASE_LIST_PAGINATION_QUERY_KEYS = ["limit", "offset"] as const;

export const CASE_LIST_QUERY_KEYS = [
  ...CASE_LIST_FILTER_QUERY_KEYS,
  ...CASE_LIST_PAGINATION_QUERY_KEYS,
] as const;

export const CASE_LIST_PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const;

export const CASE_LIST_DEFAULT_PAGE_SIZE = 50;

const STATUS_VALUES: CaseStatus[] = ["open", "pending", "resolved", "closed"];
const PRIORITY_VALUES: CasePriority[] = ["low", "normal", "high", "urgent"];
const SOURCE_VALUES: CaseSource[] = [
  "manual",
  "email",
  "chat",
  "phone",
  "web",
  "import",
];
const SLA_STATUS_VALUES: CaseSlaStatus[] = ["on_track", "at_risk", "breached"];

function parseEnumFilter<T extends string>(
  value: string | null,
  allowed: readonly T[],
): T | "" {
  if (!value) {
    return "";
  }
  return allowed.includes(value as T) ? (value as T) : "";
}

export function parseCaseListLimitParam(value: string | null): number {
  if (!value) {
    return CASE_LIST_DEFAULT_PAGE_SIZE;
  }
  const parsed = Number(value);
  if (
    !Number.isInteger(parsed) ||
    !CASE_LIST_PAGE_SIZE_OPTIONS.includes(
      parsed as (typeof CASE_LIST_PAGE_SIZE_OPTIONS)[number],
    )
  ) {
    return CASE_LIST_DEFAULT_PAGE_SIZE;
  }
  return parsed;
}

export function parseCaseListOffsetParam(value: string | null): number {
  if (!value) {
    return 0;
  }
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 0) {
    return 0;
  }
  return parsed;
}

export function parseCaseListFiltersFromSearchParams(
  searchParams: URLSearchParams,
): CaseListFilterState {
  return {
    status: parseEnumFilter(searchParams.get("status"), STATUS_VALUES),
    priority: parseEnumFilter(searchParams.get("priority"), PRIORITY_VALUES),
    source: parseEnumFilter(searchParams.get("source"), SOURCE_VALUES),
    sla_status: parseEnumFilter(
      searchParams.get("sla_status"),
      SLA_STATUS_VALUES,
    ),
    customer_id: searchParams.get("customer_id")?.trim() ?? "",
    assigned_to_user_id: searchParams.get("assigned_to_user_id")?.trim() ?? "",
  };
}

export function parseCaseListUrlState(searchParams: URLSearchParams): {
  filters: CaseListFilterState;
  pageSize: number;
  offset: number;
} {
  return {
    filters: parseCaseListFiltersFromSearchParams(searchParams),
    pageSize: parseCaseListLimitParam(searchParams.get("limit")),
    offset: parseCaseListOffsetParam(searchParams.get("offset")),
  };
}

export function buildCaseListSearchParams(
  filters: CaseListFilterState,
  pageSize: number,
  offset: number,
  currentSearchParams: URLSearchParams,
): URLSearchParams {
  const params = new URLSearchParams();
  const knownKeys = new Set<string>(CASE_LIST_QUERY_KEYS);

  currentSearchParams.forEach((value, key) => {
    if (!knownKeys.has(key)) {
      params.set(key, value);
    }
  });

  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.priority) {
    params.set("priority", filters.priority);
  }
  if (filters.source) {
    params.set("source", filters.source);
  }
  if (filters.sla_status) {
    params.set("sla_status", filters.sla_status);
  }
  if (filters.customer_id) {
    params.set("customer_id", filters.customer_id);
  }
  if (filters.assigned_to_user_id) {
    params.set("assigned_to_user_id", filters.assigned_to_user_id);
  }
  if (pageSize !== CASE_LIST_DEFAULT_PAGE_SIZE) {
    params.set("limit", String(pageSize));
  }
  if (offset > 0) {
    params.set("offset", String(offset));
  }

  return params;
}
