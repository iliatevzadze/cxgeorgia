"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { useLocale, useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";
import { getAccessToken } from "@/lib/auth/token-storage";
import {
  createCustomer,
  deleteCustomer,
  getCustomer,
  listCustomers,
  updateCustomer,
} from "@/lib/customers/api";
import type { Customer, CustomerStatus } from "@/lib/customers/types";

type WorkspaceCustomersProps = {
  workspaceId: string;
};

type CustomerFormState = {
  displayName: string;
  email: string;
  phone: string;
  externalId: string;
  locale: string;
  notes: string;
  status: CustomerStatus;
};

type StatusFilter = "all" | CustomerStatus;

const EMPTY_CREATE_FORM: CustomerFormState = {
  displayName: "",
  email: "",
  phone: "",
  externalId: "",
  locale: "",
  notes: "",
  status: "active",
};

function formatDateTime(value: string, locale: string, noValue: string): string {
  if (!value) {
    return noValue;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function trimOptional(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed || undefined;
}

function customerToForm(customer: Customer): CustomerFormState {
  return {
    displayName: customer.display_name,
    email: customer.email ?? "",
    phone: customer.phone ?? "",
    externalId: customer.external_id ?? "",
    locale: customer.locale ?? "",
    notes: customer.notes ?? "",
    status: customer.status,
  };
}

function buildCreatePayload(form: CustomerFormState) {
  return {
    display_name: form.displayName.trim(),
    email: trimOptional(form.email),
    phone: trimOptional(form.phone),
    external_id: trimOptional(form.externalId),
    locale: trimOptional(form.locale),
    notes: trimOptional(form.notes),
  };
}

function buildUpdatePayload(
  form: CustomerFormState,
  original: Customer,
): Record<string, string | null | CustomerStatus> {
  const payload: Record<string, string | null | CustomerStatus> = {};
  const displayName = form.displayName.trim();

  if (displayName !== original.display_name) {
    payload.display_name = displayName;
  }

  const email = trimOptional(form.email) ?? null;
  if (email !== original.email) {
    payload.email = email;
  }

  const phone = trimOptional(form.phone) ?? null;
  if (phone !== original.phone) {
    payload.phone = phone;
  }

  const externalId = trimOptional(form.externalId) ?? null;
  if (externalId !== original.external_id) {
    payload.external_id = externalId;
  }

  const locale = trimOptional(form.locale) ?? null;
  if (locale !== original.locale) {
    payload.locale = locale;
  }

  const notes = trimOptional(form.notes) ?? null;
  if (notes !== original.notes) {
    payload.notes = notes;
  }

  if (form.status !== original.status) {
    payload.status = form.status;
  }

  return payload;
}

export function WorkspaceCustomers({ workspaceId }: WorkspaceCustomersProps) {
  const t = useTranslations("workspaces.app.customers");
  const tCommon = useTranslations("workspaces.common");
  const locale = useLocale();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(
    null,
  );
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(
    null,
  );
  const [createForm, setCreateForm] = useState(EMPTY_CREATE_FORM);
  const [editForm, setEditForm] = useState<CustomerFormState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createValidationError, setCreateValidationError] = useState<
    string | null
  >(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveValidationError, setSaveValidationError] = useState<string | null>(
    null,
  );
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const noValue = t("noValue");

  const loadCustomers = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setLoadError(tCommon("accessDenied"));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);

    try {
      const items = await listCustomers(workspaceId, token, {
        search: appliedSearch || undefined,
        status: statusFilter === "all" ? undefined : statusFilter,
      });
      setCustomers(items);
    } catch (error) {
      setCustomers([]);

      if (error instanceof ApiError) {
        if (error.status === 404) {
          setLoadError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setLoadError(tCommon("accessDenied"));
        } else {
          setLoadError(t("error"));
        }
      } else {
        setLoadError(t("error"));
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, appliedSearch, statusFilter, t, tCommon]);

  useEffect(() => {
    void loadCustomers();
  }, [loadCustomers]);

  const loadCustomerDetail = useCallback(
    async (customerId: string) => {
      const token = getAccessToken();
      if (!token) {
        setDetailError(tCommon("accessDenied"));
        return;
      }

      setIsDetailLoading(true);
      setDetailError(null);

      try {
        const customer = await getCustomer(workspaceId, customerId, token);
        setSelectedCustomer(customer);
        setEditForm(customerToForm(customer));
      } catch (error) {
        setSelectedCustomer(null);
        setEditForm(null);

        if (error instanceof ApiError) {
          if (error.status === 404) {
            setDetailError(tCommon("notFound"));
          } else if (error.status === 401 || error.status === 403) {
            setDetailError(tCommon("accessDenied"));
          } else {
            setDetailError(t("error"));
          }
        } else {
          setDetailError(t("error"));
        }
      } finally {
        setIsDetailLoading(false);
      }
    },
    [workspaceId, t, tCommon],
  );

  useEffect(() => {
    if (selectedCustomerId) {
      void loadCustomerDetail(selectedCustomerId);
    } else {
      setSelectedCustomer(null);
      setEditForm(null);
      setDetailError(null);
    }
  }, [selectedCustomerId, loadCustomerDetail]);

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAppliedSearch(searchInput.trim());
  }

  function handleStatusFilterChange(value: StatusFilter) {
    setStatusFilter(value);
  }

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateValidationError(null);
    setCreateError(null);

    const displayName = createForm.displayName.trim();
    if (!displayName) {
      setCreateValidationError(t("displayNameRequired"));
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setCreateError(tCommon("accessDenied"));
      return;
    }

    setIsCreating(true);

    try {
      await createCustomer(workspaceId, buildCreatePayload(createForm), token);
      setCreateForm(EMPTY_CREATE_FORM);
      setSelectedCustomerId(null);
      await loadCustomers();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setCreateError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setCreateError(tCommon("accessDenied"));
        } else {
          setCreateError(t("saveError"));
        }
      } else {
        setCreateError(t("saveError"));
      }
    } finally {
      setIsCreating(false);
    }
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedCustomer || !editForm || !selectedCustomerId) {
      return;
    }

    setSaveValidationError(null);
    setSaveError(null);

    const displayName = editForm.displayName.trim();
    if (!displayName) {
      setSaveValidationError(t("displayNameRequired"));
      return;
    }

    const payload = buildUpdatePayload(editForm, selectedCustomer);
    if (Object.keys(payload).length === 0) {
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setSaveError(tCommon("accessDenied"));
      return;
    }

    setIsSaving(true);

    try {
      const updated = await updateCustomer(
        workspaceId,
        selectedCustomerId,
        payload,
        token,
      );
      setSelectedCustomer(updated);
      setEditForm(customerToForm(updated));
      await loadCustomers();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setSaveError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setSaveError(tCommon("accessDenied"));
        } else {
          setSaveError(t("saveError"));
        }
      } else {
        setSaveError(t("saveError"));
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    if (!selectedCustomerId) {
      return;
    }

    setDeleteError(null);

    const token = getAccessToken();
    if (!token) {
      setDeleteError(tCommon("accessDenied"));
      return;
    }

    setIsDeleting(true);

    try {
      await deleteCustomer(workspaceId, selectedCustomerId, token);
      setSelectedCustomerId(null);
      await loadCustomers();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setDeleteError(tCommon("notFound"));
        } else if (error.status === 401 || error.status === 403) {
          setDeleteError(tCommon("accessDenied"));
        } else {
          setDeleteError(t("deleteError"));
        }
      } else {
        setDeleteError(t("deleteError"));
      }
    } finally {
      setIsDeleting(false);
    }
  }

  function statusLabel(status: CustomerStatus): string {
    return status === "archived" ? t("statusArchived") : t("statusActive");
  }

  const isBusy = isCreating || isSaving || isDeleting || isDetailLoading;

  return (
    <div className="workspace-customers-page">
      <section className="workspace-panel workspace-customers-create-panel">
        <h2>{t("createTitle")}</h2>

        {createError ? (
          <p className="workspace-error" role="alert">
            {createError}
          </p>
        ) : null}

        {createValidationError ? (
          <p className="workspace-error" role="alert">
            {createValidationError}
          </p>
        ) : null}

        <form
          className="workspace-form workspace-customers-form"
          onSubmit={(event) => void handleCreateSubmit(event)}
        >
          <label className="auth-field">
            <span>{t("displayName")}</span>
            <input
              type="text"
              name="displayName"
              value={createForm.displayName}
              disabled={isBusy}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  displayName: event.target.value,
                }))
              }
            />
          </label>
          <label className="auth-field">
            <span>{t("email")}</span>
            <input
              type="email"
              name="email"
              value={createForm.email}
              disabled={isBusy}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  email: event.target.value,
                }))
              }
            />
          </label>
          <label className="auth-field">
            <span>{t("phone")}</span>
            <input
              type="text"
              name="phone"
              value={createForm.phone}
              disabled={isBusy}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  phone: event.target.value,
                }))
              }
            />
          </label>
          <label className="auth-field">
            <span>{t("externalId")}</span>
            <input
              type="text"
              name="externalId"
              value={createForm.externalId}
              disabled={isBusy}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  externalId: event.target.value,
                }))
              }
            />
          </label>
          <label className="auth-field">
            <span>{t("locale")}</span>
            <input
              type="text"
              name="locale"
              value={createForm.locale}
              disabled={isBusy}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  locale: event.target.value,
                }))
              }
            />
          </label>
          <label className="auth-field">
            <span>{t("notes")}</span>
            <textarea
              name="notes"
              rows={3}
              value={createForm.notes}
              disabled={isBusy}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
            />
          </label>
          <button type="submit" className="auth-submit" disabled={isBusy}>
            {isCreating ? t("creating") : t("createButton")}
          </button>
        </form>
      </section>

      <section className="workspace-panel workspace-customers-list-panel">
        <h1>{t("title")}</h1>

        <form
          className="workspace-form workspace-customers-filters"
          onSubmit={(event) => void handleSearchSubmit(event)}
        >
          <label className="auth-field">
            <span>{t("searchLabel")}</span>
            <input
              type="search"
              name="search"
              value={searchInput}
              disabled={isLoading}
              onChange={(event) => setSearchInput(event.target.value)}
            />
          </label>
          <label className="auth-field">
            <span>{t("statusLabel")}</span>
            <select
              name="statusFilter"
              value={statusFilter}
              disabled={isLoading}
              onChange={(event) =>
                handleStatusFilterChange(event.target.value as StatusFilter)
              }
            >
              <option value="all">{t("statusAll")}</option>
              <option value="active">{t("statusActive")}</option>
              <option value="archived">{t("statusArchived")}</option>
            </select>
          </label>
          <button type="submit" className="auth-submit" disabled={isLoading}>
            {t("applySearch")}
          </button>
        </form>

        {isLoading ? (
          <p className="workspace-status">{t("loading")}</p>
        ) : loadError ? (
          <p className="workspace-error" role="alert">
            {loadError}
          </p>
        ) : customers.length === 0 ? (
          <p className="workspace-empty">{t("empty")}</p>
        ) : (
          <ul className="workspace-customers-list">
            {customers.map((customer) => (
              <li key={customer.id} className="workspace-customers-item">
                <button
                  type="button"
                  className={
                    selectedCustomerId === customer.id
                      ? "workspace-customers-select is-selected"
                      : "workspace-customers-select"
                  }
                  disabled={isBusy}
                  onClick={() => setSelectedCustomerId(customer.id)}
                >
                  <span className="workspace-customers-item-name">
                    {customer.display_name}
                  </span>
                  <dl className="account-details">
                    <div>
                      <dt>{t("email")}</dt>
                      <dd>{customer.email ?? noValue}</dd>
                    </div>
                    <div>
                      <dt>{t("phone")}</dt>
                      <dd>{customer.phone ?? noValue}</dd>
                    </div>
                    <div>
                      <dt>{t("statusLabel")}</dt>
                      <dd>{statusLabel(customer.status)}</dd>
                    </div>
                    <div>
                      <dt>{t("createdAtLabel")}</dt>
                      <dd>
                        {formatDateTime(customer.created_at, locale, noValue)}
                      </dd>
                    </div>
                  </dl>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedCustomerId ? (
        <section className="workspace-panel workspace-customers-edit-panel">
          <h2>{t("editTitle")}</h2>

          {detailError ? (
            <p className="workspace-error" role="alert">
              {detailError}
            </p>
          ) : null}

          {saveError ? (
            <p className="workspace-error" role="alert">
              {saveError}
            </p>
          ) : null}

          {deleteError ? (
            <p className="workspace-error" role="alert">
              {deleteError}
            </p>
          ) : null}

          {saveValidationError ? (
            <p className="workspace-error" role="alert">
              {saveValidationError}
            </p>
          ) : null}

          {isDetailLoading || !editForm ? (
            <p className="workspace-status">{t("detailLoading")}</p>
          ) : (
            <>
              <form
                className="workspace-form workspace-customers-form"
                onSubmit={(event) => void handleEditSubmit(event)}
              >
                <label className="auth-field">
                  <span>{t("displayName")}</span>
                  <input
                    type="text"
                    name="editDisplayName"
                    value={editForm.displayName}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? { ...current, displayName: event.target.value }
                          : current,
                      )
                    }
                  />
                </label>
                <label className="auth-field">
                  <span>{t("email")}</span>
                  <input
                    type="email"
                    name="editEmail"
                    value={editForm.email}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? { ...current, email: event.target.value }
                          : current,
                      )
                    }
                  />
                </label>
                <label className="auth-field">
                  <span>{t("phone")}</span>
                  <input
                    type="text"
                    name="editPhone"
                    value={editForm.phone}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? { ...current, phone: event.target.value }
                          : current,
                      )
                    }
                  />
                </label>
                <label className="auth-field">
                  <span>{t("externalId")}</span>
                  <input
                    type="text"
                    name="editExternalId"
                    value={editForm.externalId}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? { ...current, externalId: event.target.value }
                          : current,
                      )
                    }
                  />
                </label>
                <label className="auth-field">
                  <span>{t("locale")}</span>
                  <input
                    type="text"
                    name="editLocale"
                    value={editForm.locale}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? { ...current, locale: event.target.value }
                          : current,
                      )
                    }
                  />
                </label>
                <label className="auth-field">
                  <span>{t("notes")}</span>
                  <textarea
                    name="editNotes"
                    rows={3}
                    value={editForm.notes}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? { ...current, notes: event.target.value }
                          : current,
                      )
                    }
                  />
                </label>
                <label className="auth-field">
                  <span>{t("statusLabel")}</span>
                  <select
                    name="editStatus"
                    value={editForm.status}
                    disabled={isBusy}
                    onChange={(event) =>
                      setEditForm((current) =>
                        current
                          ? {
                              ...current,
                              status: event.target.value as CustomerStatus,
                            }
                          : current,
                      )
                    }
                  >
                    <option value="active">{t("statusActive")}</option>
                    <option value="archived">{t("statusArchived")}</option>
                  </select>
                </label>
                <button type="submit" className="auth-submit" disabled={isBusy}>
                  {isSaving ? t("saving") : t("saveButton")}
                </button>
              </form>

              <button
                type="button"
                className="workspace-customers-delete-button"
                disabled={isBusy}
                onClick={() => void handleDelete()}
              >
                {isDeleting ? t("deleting") : t("deleteButton")}
              </button>
            </>
          )}
        </section>
      ) : null}
    </div>
  );
}
