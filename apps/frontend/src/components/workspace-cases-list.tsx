"use client";

import { useCallback, useEffect, useState } from "react";

import { useSearchParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";

import { Link, usePathname, useRouter } from "@/i18n/navigation";

import { WorkspaceCaseCreateForm } from "@/components/workspace-case-create-form";
import { ApiError } from "@/lib/api/errors";
import { listCases } from "@/lib/cases/api";
import {
  buildCaseListSearchParams,
  CASE_LIST_PAGE_SIZE_OPTIONS,
  CASE_LIST_SORT_BY_OPTIONS,
  CASE_LIST_SORT_ORDER_OPTIONS,
  EMPTY_CASE_LIST_FILTERS,
  parseCaseListUrlState,
  type CaseListFilterState,
} from "@/lib/cases/list-url-state";
import type {
  CaseListFilters,
  CaseListSortBy,
  CaseListSortOrder,
  CasePriority,
  CaseSlaStatus,
  CaseSource,
  CaseStatus,
  UniversalCaseRead,
} from "@/lib/cases/types";
import { getAccessToken } from "@/lib/auth/token-storage";
import { listCustomers } from "@/lib/customers/api";
import type { Customer } from "@/lib/customers/types";
import { listWorkspaceMemberships } from "@/lib/workspaces/api";
import type { WorkspaceMembershipRead } from "@/lib/workspaces/types";
import { workspaceRoutes } from "@/lib/workspaces/routes";

type WorkspaceCasesListProps = {
  workspaceId: string;
};

const STATUS_OPTIONS: CaseStatus[] = [
  "open",
  "pending",
  "resolved",
  "closed",
];

const PRIORITY_OPTIONS: CasePriority[] = [
  "low",
  "normal",
  "high",
  "urgent",
];

const SOURCE_OPTIONS: CaseSource[] = [
  "manual",
  "email",
  "chat",
  "phone",
  "web",
  "import",
];

const SLA_STATUS_OPTIONS: CaseSlaStatus[] = [
  "on_track",
  "at_risk",
  "breached",
];

function buildCaseListFilters(state: CaseListFilterState): CaseListFilters {
  const filters: CaseListFilters = {};
  if (state.status) {
    filters.status = state.status;
  }
  if (state.priority) {
    filters.priority = state.priority;
  }
  if (state.source) {
    filters.source = state.source;
  }
  if (state.sla_status) {
    filters.sla_status = state.sla_status;
  }
  if (state.customer_id) {
    filters.customer_id = state.customer_id;
  }
  if (state.assigned_to_user_id) {
    filters.assigned_to_user_id = state.assigned_to_user_id;
  }
  return filters;
}

function formatMemberLabel(membership: WorkspaceMembershipRead): string {
  return `${membership.user_id} (${membership.role})`;
}

function formatCustomerOptionLabel(customer: Customer): string {
  if (customer.email) {
    return `${customer.display_name} (${customer.email})`;
  }
  return customer.display_name;
}

function formatCreatedAt(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatCustomer(item: UniversalCaseRead, fallback: string): string {
  return item.customer_name ?? item.customer_email ?? fallback;
}

function slaBadgeClassName(slaStatus: CaseSlaStatus | null): string {
  if (!slaStatus) {
    return "workspace-case-sla-badge workspace-case-sla-badge--not-set";
  }
  return `workspace-case-sla-badge workspace-case-sla-badge--${slaStatus.replace(/_/g, "-")}`;
}

function formatSlaStatusLabel(
  slaStatus: CaseSlaStatus | null,
  translate: (key: string) => string,
): string {
  if (!slaStatus) {
    return translate("notSet");
  }
  return translate(`slaStatusOptions.${slaStatus}`);
}

export function WorkspaceCasesList({ workspaceId }: WorkspaceCasesListProps) {
  const t = useTranslations("workspaces.app.cases");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const { filters, pageSize, offset, sortBy, sortOrder } = parseCaseListUrlState(
    new URLSearchParams(searchParams.toString()),
  );

  const [cases, setCases] = useState<UniversalCaseRead[]>([]);
  const [listTotal, setListTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isCustomersLoading, setIsCustomersLoading] = useState(true);
  const [customersLoadError, setCustomersLoadError] = useState<string | null>(
    null,
  );
  const [memberships, setMemberships] = useState<WorkspaceMembershipRead[]>(
    [],
  );
  const [isMembershipsLoading, setIsMembershipsLoading] = useState(true);
  const [assigneesLoadError, setAssigneesLoadError] = useState<string | null>(
    null,
  );

  const replaceListUrl = useCallback(
    (next: {
      filters: CaseListFilterState;
      pageSize: number;
      offset: number;
      sortBy: CaseListSortBy;
      sortOrder: CaseListSortOrder;
    }) => {
      const params = buildCaseListSearchParams(
        next.filters,
        next.pageSize,
        next.offset,
        next.sortBy,
        next.sortOrder,
        new URLSearchParams(searchParams.toString()),
      );
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname);
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    let isMounted = true;

    async function loadCustomers() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setIsCustomersLoading(false);
        }
        return;
      }

      setIsCustomersLoading(true);
      setCustomersLoadError(null);

      try {
        const items = await listCustomers(workspaceId, token, {
          status: "active",
        });
        if (isMounted) {
          setCustomers(items);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setCustomers([]);

        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403) {
            setCustomersLoadError(tCommon("accessDenied"));
          } else if (error.status === 404) {
            setCustomersLoadError(tCommon("notFound"));
          } else {
            setCustomersLoadError(t("create.customersLoadError"));
          }
        } else {
          setCustomersLoadError(t("create.customersLoadError"));
        }
      } finally {
        if (isMounted) {
          setIsCustomersLoading(false);
        }
      }
    }

    void loadCustomers();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, t, tCommon]);

  useEffect(() => {
    let isMounted = true;

    async function loadMemberships() {
      const token = getAccessToken();
      if (!token) {
        if (isMounted) {
          setIsMembershipsLoading(false);
        }
        return;
      }

      setIsMembershipsLoading(true);
      setAssigneesLoadError(null);

      try {
        const items = await listWorkspaceMemberships(workspaceId, token);
        if (isMounted) {
          setMemberships(items.filter((item) => item.status === "active"));
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setMemberships([]);

        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403) {
            setAssigneesLoadError(tCommon("accessDenied"));
          } else if (error.status === 404) {
            setAssigneesLoadError(tCommon("notFound"));
          } else {
            setAssigneesLoadError(t("assigneesLoadError"));
          }
        } else {
          setAssigneesLoadError(t("assigneesLoadError"));
        }
      } finally {
        if (isMounted) {
          setIsMembershipsLoading(false);
        }
      }
    }

    void loadMemberships();

    return () => {
      isMounted = false;
    };
  }, [workspaceId, t, tCommon]);

  const loadCases = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setErrorMessage(tCommon("accessDenied"));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const page = await listCases(workspaceId, token, {
        ...buildCaseListFilters(filters),
        limit: pageSize,
        offset,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setCases(page.items);
      setListTotal(page.total);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setErrorMessage(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setErrorMessage(tCommon("accessDenied"));
        } else {
          setErrorMessage(t("error"));
        }
      } else {
        setErrorMessage(t("error"));
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, filters, offset, pageSize, sortBy, sortOrder, t, tCommon]);

  useEffect(() => {
    void loadCases();
  }, [loadCases, refreshToken]);

  function handleCaseCreated() {
    replaceListUrl({ filters, pageSize, offset: 0, sortBy, sortOrder });
    setRefreshToken((current) => current + 1);
  }

  function handleFilterChange(
    field: keyof CaseListFilterState,
    value: string,
  ) {
    replaceListUrl({
      filters: {
        ...filters,
        [field]: value,
      },
      pageSize,
      offset: 0,
      sortBy,
      sortOrder,
    });
  }

  function handleClearFilters() {
    replaceListUrl({
      filters: EMPTY_CASE_LIST_FILTERS,
      pageSize,
      offset: 0,
      sortBy,
      sortOrder,
    });
  }

  function handlePageSizeChange(value: string) {
    replaceListUrl({
      filters,
      pageSize: Number(value),
      offset: 0,
      sortBy,
      sortOrder,
    });
  }

  function handleSortByChange(value: string) {
    replaceListUrl({
      filters,
      pageSize,
      offset: 0,
      sortBy: value as CaseListSortBy,
      sortOrder,
    });
  }

  function handleSortOrderChange(value: string) {
    replaceListUrl({
      filters,
      pageSize,
      offset: 0,
      sortBy,
      sortOrder: value as CaseListSortOrder,
    });
  }

  function handlePreviousPage() {
    replaceListUrl({
      filters,
      pageSize,
      offset: Math.max(0, offset - pageSize),
      sortBy,
      sortOrder,
    });
  }

  function handleNextPage() {
    replaceListUrl({
      filters,
      pageSize,
      offset: offset + pageSize,
      sortBy,
      sortOrder,
    });
  }

  const canGoPrevious = offset > 0;
  const canGoNext = offset + pageSize < listTotal;
  const pageNumber =
    pageSize > 0 ? Math.floor(offset / pageSize) + 1 : 1;

  return (
    <div className="workspace-cases-page">
      <WorkspaceCaseCreateForm
        workspaceId={workspaceId}
        onCreated={handleCaseCreated}
      />

      {isLoading ? (
        <p className="workspace-status">{t("loading")}</p>
      ) : errorMessage ? (
        <section className="workspace-panel">
          <p className="workspace-error" role="alert">
            {errorMessage}
          </p>
        </section>
      ) : (
        <section className="workspace-panel">
          <h1>{t("title")}</h1>
          <p className="workspace-description">{t("description")}</p>

          <div
            className="workspace-cases-filters"
            aria-label={t("filterCases")}
          >
            <h2>{t("filtersLabel")}</h2>
            <label className="auth-field">
              <span>{t("statusLabel")}</span>
              <select
                name="statusFilter"
                value={filters.status}
                disabled={isLoading}
                onChange={(event) =>
                  handleFilterChange("status", event.target.value)
                }
              >
                <option value="">{t("allStatuses")}</option>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {t(`detail.statusOptions.${option}`)}
                  </option>
                ))}
              </select>
            </label>
            <label className="auth-field">
              <span>{t("priorityLabel")}</span>
              <select
                name="priorityFilter"
                value={filters.priority}
                disabled={isLoading}
                onChange={(event) =>
                  handleFilterChange("priority", event.target.value)
                }
              >
                <option value="">{t("allPriorities")}</option>
                {PRIORITY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {t(`create.priorityOptions.${option}`)}
                  </option>
                ))}
              </select>
            </label>
            <label className="auth-field">
              <span>{t("sourceLabel")}</span>
              <select
                name="sourceFilter"
                value={filters.source}
                disabled={isLoading}
                onChange={(event) =>
                  handleFilterChange("source", event.target.value)
                }
              >
                <option value="">{t("allSources")}</option>
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {t(`create.sourceOptions.${option}`)}
                  </option>
                ))}
              </select>
            </label>
            <label className="auth-field">
              <span>{t("slaStatusLabel")}</span>
              <select
                name="slaStatusFilter"
                value={filters.sla_status}
                disabled={isLoading}
                onChange={(event) =>
                  handleFilterChange("sla_status", event.target.value)
                }
              >
                <option value="">{t("allSlaStatuses")}</option>
                {SLA_STATUS_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {t(`slaStatusOptions.${option}`)}
                  </option>
                ))}
              </select>
            </label>
            <label className="auth-field">
              <span>{t("customerLabel")}</span>
              {customersLoadError ? (
                <p className="workspace-error workspace-cases-filter-error" role="alert">
                  {customersLoadError}
                </p>
              ) : null}
              {isCustomersLoading ? (
                <p className="workspace-status">{t("create.customersLoading")}</p>
              ) : (
                <select
                  name="customerFilter"
                  value={filters.customer_id}
                  disabled={isLoading || Boolean(customersLoadError)}
                  onChange={(event) =>
                    handleFilterChange("customer_id", event.target.value)
                  }
                >
                  <option value="">{t("allCustomers")}</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {formatCustomerOptionLabel(customer)}
                    </option>
                  ))}
                </select>
              )}
            </label>
            <label className="auth-field">
              <span>{t("assignedUserLabel")}</span>
              {assigneesLoadError ? (
                <p className="workspace-error workspace-cases-filter-error" role="alert">
                  {assigneesLoadError}
                </p>
              ) : null}
              {isMembershipsLoading ? (
                <p className="workspace-status">{t("detail.assignmentLoading")}</p>
              ) : (
                <select
                  name="assigneeFilter"
                  value={filters.assigned_to_user_id}
                  disabled={isLoading || Boolean(assigneesLoadError)}
                  onChange={(event) =>
                    handleFilterChange("assigned_to_user_id", event.target.value)
                  }
                >
                  <option value="">{t("allAssignees")}</option>
                  {memberships.map((membership) => (
                    <option key={membership.id} value={membership.user_id}>
                      {formatMemberLabel(membership)}
                    </option>
                  ))}
                </select>
              )}
            </label>
            <button
              type="button"
              className="auth-submit"
              disabled={isLoading}
              onClick={handleClearFilters}
            >
              {t("clearFilters")}
            </button>
          </div>

          <p className="workspace-cases-total">
            {t("totalCasesLabel")}: {listTotal}
          </p>

          <div
            className="workspace-cases-sorting"
            aria-label={t("sortCases")}
          >
            <label className="auth-field">
              <span>{t("sortByLabel")}</span>
              <select
                name="sortBy"
                value={sortBy}
                disabled={isLoading}
                onChange={(event) => handleSortByChange(event.target.value)}
              >
                {CASE_LIST_SORT_BY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {t(`sortByOptions.${option}`)}
                  </option>
                ))}
              </select>
            </label>
            <label className="auth-field">
              <span>{t("sortOrderLabel")}</span>
              <select
                name="sortOrder"
                value={sortOrder}
                disabled={isLoading}
                onChange={(event) => handleSortOrderChange(event.target.value)}
              >
                {CASE_LIST_SORT_ORDER_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {t(`sortOrderOptions.${option}`)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {cases.length === 0 ? (
            <div className="workspace-empty">
              <p>{t("emptyTitle")}</p>
              <p>{t("emptyMessage")}</p>
            </div>
          ) : (
            <ul className="workspace-cases">
              {cases.map((item) => (
                <li key={item.id} className="workspace-case-item">
                  <h2>
                    <Link href={workspaceRoutes.appCaseDetail(workspaceId, item.id)}>
                      {item.title}
                    </Link>
                  </h2>
                  <dl className="account-details">
                    <div>
                      <dt>{t("slaStatusLabel")}</dt>
                      <dd>
                        <span className={slaBadgeClassName(item.sla_status)}>
                          {formatSlaStatusLabel(item.sla_status, t)}
                        </span>
                      </dd>
                    </div>
                    <div>
                      <dt>{t("statusLabel")}</dt>
                      <dd>{item.status}</dd>
                    </div>
                    <div>
                      <dt>{t("priorityLabel")}</dt>
                      <dd>{item.priority}</dd>
                    </div>
                    <div>
                      <dt>{t("sourceLabel")}</dt>
                      <dd>{item.source}</dd>
                    </div>
                    <div>
                      <dt>{t("customerLabel")}</dt>
                      <dd>{formatCustomer(item, t("noCustomer"))}</dd>
                    </div>
                    <div>
                      <dt>{t("createdAtLabel")}</dt>
                      <dd>{formatCreatedAt(item.created_at, locale)}</dd>
                    </div>
                  </dl>
                </li>
              ))}
            </ul>
          )}

          <nav
            className="workspace-cases-pagination"
            aria-label={t("pageLabel")}
          >
            <label className="auth-field">
              <span>{t("pageSizeLabel")}</span>
              <select
                name="pageSize"
                value={pageSize}
                disabled={isLoading}
                aria-label={t("casesPerPageLabel")}
                onChange={(event) => handlePageSizeChange(event.target.value)}
              >
                {CASE_LIST_PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="auth-submit"
              disabled={isLoading || !canGoPrevious}
              onClick={handlePreviousPage}
            >
              {t("previousPage")}
            </button>
            <span>
              {t("pageLabel")}: {pageNumber}
            </span>
            <button
              type="button"
              className="auth-submit"
              disabled={isLoading || !canGoNext}
              onClick={handleNextPage}
            >
              {t("nextPage")}
            </button>
          </nav>
        </section>
      )}
    </div>
  );
}
