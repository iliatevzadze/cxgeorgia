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
  CASE_LIST_DEFAULT_SORT_BY,
  CASE_LIST_DEFAULT_SORT_ORDER,
  CASE_LIST_PAGE_SIZE_OPTIONS,
  CASE_LIST_SORT_BY_OPTIONS,
  CASE_LIST_SORT_ORDER_OPTIONS,
  EMPTY_CASE_LIST_FILTERS,
  parseCaseListUrlState,
  type CaseListFilterState,
} from "@/lib/cases/list-url-state";
import {
  createCaseListView,
  deleteCaseListView,
  listCaseListViews,
  updateCaseListView,
} from "@/lib/cases/saved-views-api";
import type {
  CaseListViewFilters,
  CaseListViewPageSize,
  CaseListViewRead,
} from "@/lib/cases/saved-views-types";
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

function filterStateToSavedViewFilters(
  state: CaseListFilterState,
): CaseListViewFilters {
  const filters: CaseListViewFilters = {};
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

function savedViewFiltersToState(filters: CaseListViewFilters): CaseListFilterState {
  return {
    status: filters.status ?? "",
    priority: filters.priority ?? "",
    source: filters.source ?? "",
    sla_status: filters.sla_status ?? "",
    customer_id: filters.customer_id ?? "",
    assigned_to_user_id: filters.assigned_to_user_id ?? "",
  };
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
  const [savedViews, setSavedViews] = useState<CaseListViewRead[]>([]);
  const [isSavedViewsLoading, setIsSavedViewsLoading] = useState(true);
  const [savedViewsLoadError, setSavedViewsLoadError] = useState<string | null>(
    null,
  );
  const [selectedSavedViewId, setSelectedSavedViewId] = useState("");
  const [saveViewName, setSaveViewName] = useState("");
  const [saveViewDescription, setSaveViewDescription] = useState("");
  const [isSavingView, setIsSavingView] = useState(false);
  const [saveViewError, setSaveViewError] = useState<string | null>(null);
  const [saveViewSuccess, setSaveViewSuccess] = useState<string | null>(null);
  const [isEditingView, setIsEditingView] = useState(false);
  const [editViewName, setEditViewName] = useState("");
  const [editViewDescription, setEditViewDescription] = useState("");
  const [isUpdatingView, setIsUpdatingView] = useState(false);
  const [updateViewError, setUpdateViewError] = useState<string | null>(null);
  const [updateViewSuccess, setUpdateViewSuccess] = useState<string | null>(
    null,
  );
  const [isDeleteConfirming, setIsDeleteConfirming] = useState(false);
  const [isDeletingView, setIsDeletingView] = useState(false);
  const [deleteViewError, setDeleteViewError] = useState<string | null>(null);
  const [deleteViewSuccess, setDeleteViewSuccess] = useState<string | null>(
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

  const loadSavedViews = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setIsSavedViewsLoading(false);
      return;
    }

    setIsSavedViewsLoading(true);
    setSavedViewsLoadError(null);

    try {
      const items = await listCaseListViews(workspaceId, token);
      setSavedViews(items);
    } catch (error) {
      setSavedViews([]);
      if (error instanceof ApiError) {
        if (error.status === 401 || error.status === 403) {
          setSavedViewsLoadError(tCommon("accessDenied"));
        } else if (error.status === 404) {
          setSavedViewsLoadError(tCommon("notFound"));
        } else {
          setSavedViewsLoadError(t("savedViewsLoadError"));
        }
      } else {
        setSavedViewsLoadError(t("savedViewsLoadError"));
      }
    } finally {
      setIsSavedViewsLoading(false);
    }
  }, [workspaceId, t, tCommon]);

  useEffect(() => {
    void loadSavedViews();
  }, [loadSavedViews]);

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

  function handleApplySavedView() {
    const view = savedViews.find((item) => item.id === selectedSavedViewId);
    if (!view) {
      return;
    }

    replaceListUrl({
      filters: savedViewFiltersToState(view.filters),
      pageSize: view.page_size ?? pageSize,
      offset: 0,
      sortBy: view.sort_by ?? CASE_LIST_DEFAULT_SORT_BY,
      sortOrder: view.sort_order ?? CASE_LIST_DEFAULT_SORT_ORDER,
    });
  }

  function handleSavedViewSelectChange(value: string) {
    setSelectedSavedViewId(value);
    setIsEditingView(false);
    setIsDeleteConfirming(false);
    setUpdateViewError(null);
    setUpdateViewSuccess(null);
    setDeleteViewError(null);
    setDeleteViewSuccess(null);
  }

  function handleStartEditView() {
    const view = savedViews.find((item) => item.id === selectedSavedViewId);
    if (!view) {
      return;
    }

    setEditViewName(view.name);
    setEditViewDescription(view.description ?? "");
    setIsEditingView(true);
    setIsDeleteConfirming(false);
    setUpdateViewError(null);
    setUpdateViewSuccess(null);
  }

  function handleCancelEditView() {
    setIsEditingView(false);
    setUpdateViewError(null);
    setUpdateViewSuccess(null);
  }

  async function handleUpdateView() {
    const trimmedName = editViewName.trim();
    if (!trimmedName) {
      setUpdateViewError(t("viewNameRequired"));
      setUpdateViewSuccess(null);
      return;
    }

    if (!selectedSavedViewId) {
      setUpdateViewError(t("noSavedViewSelected"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setUpdateViewError(tCommon("accessDenied"));
      return;
    }

    setIsUpdatingView(true);
    setUpdateViewError(null);
    setUpdateViewSuccess(null);

    const trimmedDescription = editViewDescription.trim();

    try {
      await updateCaseListView(
        workspaceId,
        selectedSavedViewId,
        {
          name: trimmedName,
          description: trimmedDescription || null,
        },
        token,
      );
      await loadSavedViews();
      setIsEditingView(false);
      setUpdateViewSuccess(t("savedViewUpdated"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 422 && typeof error.message === "string") {
          setUpdateViewError(error.message);
        } else if (error.status === 401 || error.status === 403) {
          setUpdateViewError(tCommon("accessDenied"));
        } else if (error.status === 404) {
          setUpdateViewError(tCommon("notFound"));
        } else {
          setUpdateViewError(t("updateViewFailed"));
        }
      } else {
        setUpdateViewError(t("updateViewFailed"));
      }
    } finally {
      setIsUpdatingView(false);
    }
  }

  function handleStartDeleteView() {
    if (!selectedSavedViewId) {
      return;
    }

    setIsDeleteConfirming(true);
    setIsEditingView(false);
    setDeleteViewError(null);
    setDeleteViewSuccess(null);
  }

  function handleCancelDeleteView() {
    setIsDeleteConfirming(false);
    setDeleteViewError(null);
  }

  async function handleConfirmDeleteView() {
    if (!selectedSavedViewId) {
      setDeleteViewError(t("noSavedViewSelected"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setDeleteViewError(tCommon("accessDenied"));
      return;
    }

    setIsDeletingView(true);
    setDeleteViewError(null);
    setDeleteViewSuccess(null);

    const deletedViewId = selectedSavedViewId;

    try {
      await deleteCaseListView(workspaceId, deletedViewId, token);
      await loadSavedViews();
      setSelectedSavedViewId("");
      setIsDeleteConfirming(false);
      setDeleteViewSuccess(t("savedViewDeleted"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 422 && typeof error.message === "string") {
          setDeleteViewError(error.message);
        } else if (error.status === 401 || error.status === 403) {
          setDeleteViewError(tCommon("accessDenied"));
        } else if (error.status === 404) {
          setDeleteViewError(tCommon("notFound"));
        } else {
          setDeleteViewError(t("deleteViewFailed"));
        }
      } else {
        setDeleteViewError(t("deleteViewFailed"));
      }
    } finally {
      setIsDeletingView(false);
    }
  }

  async function handleSaveView() {
    const trimmedName = saveViewName.trim();
    if (!trimmedName) {
      setSaveViewError(t("viewNameRequired"));
      setSaveViewSuccess(null);
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setSaveViewError(tCommon("accessDenied"));
      return;
    }

    setIsSavingView(true);
    setSaveViewError(null);
    setSaveViewSuccess(null);

    const trimmedDescription = saveViewDescription.trim();

    try {
      const created = await createCaseListView(
        workspaceId,
        {
          name: trimmedName,
          description: trimmedDescription || null,
          filters: filterStateToSavedViewFilters(filters),
          sort_by: sortBy,
          sort_order: sortOrder,
          page_size: pageSize as CaseListViewPageSize,
        },
        token,
      );
      await loadSavedViews();
      setSelectedSavedViewId(created.id);
      setSaveViewName("");
      setSaveViewDescription("");
      setSaveViewSuccess(t("savedViewCreated"));
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 422 && typeof error.message === "string") {
          setSaveViewError(error.message);
        } else if (error.status === 401 || error.status === 403) {
          setSaveViewError(tCommon("accessDenied"));
        } else if (error.status === 404) {
          setSaveViewError(tCommon("notFound"));
        } else {
          setSaveViewError(t("saveViewFailed"));
        }
      } else {
        setSaveViewError(t("saveViewFailed"));
      }
    } finally {
      setIsSavingView(false);
    }
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

          <div
            className="workspace-cases-saved-views"
            aria-label={t("savedViewsLabel")}
          >
            <h2>{t("savedViewsLabel")}</h2>
            {savedViewsLoadError ? (
              <p
                className="workspace-error workspace-cases-filter-error"
                role="alert"
              >
                {savedViewsLoadError}
              </p>
            ) : null}
            {isSavedViewsLoading ? (
              <p className="workspace-status">{t("loading")}</p>
            ) : savedViews.length === 0 ? (
              <p className="workspace-status">{t("noSavedViewsYet")}</p>
            ) : (
              <label className="auth-field">
                <span>{t("selectSavedView")}</span>
                <select
                  name="savedViewSelect"
                  value={selectedSavedViewId}
                  disabled={isLoading}
                  onChange={(event) =>
                    handleSavedViewSelectChange(event.target.value)
                  }
                >
                  <option value="">{t("selectSavedView")}</option>
                  {savedViews.map((view) => (
                    <option key={view.id} value={view.id}>
                      {view.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <button
              type="button"
              className="auth-submit"
              disabled={
                isLoading || !selectedSavedViewId || isSavedViewsLoading
              }
              onClick={handleApplySavedView}
            >
              {t("applyView")}
            </button>
            <button
              type="button"
              className="auth-submit"
              disabled={
                isLoading ||
                !selectedSavedViewId ||
                isSavedViewsLoading ||
                isUpdatingView ||
                isDeletingView
              }
              onClick={handleStartEditView}
            >
              {t("editSelectedView")}
            </button>
            <button
              type="button"
              className="auth-submit"
              disabled={
                isLoading ||
                !selectedSavedViewId ||
                isSavedViewsLoading ||
                isUpdatingView ||
                isDeletingView
              }
              onClick={handleStartDeleteView}
            >
              {t("deleteSelectedView")}
            </button>

            {isEditingView ? (
              <>
                <h3>{t("editSelectedView")}</h3>
                <label className="auth-field">
                  <span>{t("viewNameLabel")}</span>
                  <input
                    type="text"
                    name="editViewName"
                    value={editViewName}
                    disabled={isUpdatingView}
                    onChange={(event) => setEditViewName(event.target.value)}
                  />
                </label>
                <label className="auth-field">
                  <span>{t("viewDescriptionLabel")}</span>
                  <input
                    type="text"
                    name="editViewDescription"
                    value={editViewDescription}
                    disabled={isUpdatingView}
                    onChange={(event) =>
                      setEditViewDescription(event.target.value)
                    }
                  />
                </label>
                {updateViewError ? (
                  <p className="workspace-error" role="alert">
                    {updateViewError}
                  </p>
                ) : null}
                {updateViewSuccess ? (
                  <p className="workspace-status">{updateViewSuccess}</p>
                ) : null}
                <button
                  type="button"
                  className="auth-submit"
                  disabled={isUpdatingView || isLoading}
                  onClick={() => void handleUpdateView()}
                >
                  {isUpdatingView ? t("updatingView") : t("saveViewChanges")}
                </button>
                <button
                  type="button"
                  className="auth-submit"
                  disabled={isUpdatingView}
                  onClick={handleCancelEditView}
                >
                  {t("cancelEdit")}
                </button>
              </>
            ) : null}

            {isDeleteConfirming ? (
              <>
                <p className="workspace-status">{t("deleteConfirmationText")}</p>
                {deleteViewError ? (
                  <p className="workspace-error" role="alert">
                    {deleteViewError}
                  </p>
                ) : null}
                {deleteViewSuccess ? (
                  <p className="workspace-status">{deleteViewSuccess}</p>
                ) : null}
                <button
                  type="button"
                  className="auth-submit"
                  disabled={isDeletingView || isLoading}
                  onClick={() => void handleConfirmDeleteView()}
                >
                  {isDeletingView ? t("deletingView") : t("confirmDelete")}
                </button>
                <button
                  type="button"
                  className="auth-submit"
                  disabled={isDeletingView}
                  onClick={handleCancelDeleteView}
                >
                  {t("cancelDelete")}
                </button>
              </>
            ) : null}

            <h3>{t("saveCurrentView")}</h3>
            <label className="auth-field">
              <span>{t("viewNameLabel")}</span>
              <input
                type="text"
                name="saveViewName"
                value={saveViewName}
                disabled={isSavingView}
                onChange={(event) => setSaveViewName(event.target.value)}
              />
            </label>
            <label className="auth-field">
              <span>{t("viewDescriptionLabel")}</span>
              <input
                type="text"
                name="saveViewDescription"
                value={saveViewDescription}
                disabled={isSavingView}
                onChange={(event) => setSaveViewDescription(event.target.value)}
              />
            </label>
            {saveViewError ? (
              <p className="workspace-error" role="alert">{saveViewError}</p>
            ) : null}
            {saveViewSuccess ? (
              <p className="workspace-status">{saveViewSuccess}</p>
            ) : null}
            <button
              type="button"
              className="auth-submit"
              disabled={isSavingView || isLoading}
              onClick={() => void handleSaveView()}
            >
              {isSavingView ? t("savingView") : t("saveView")}
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
