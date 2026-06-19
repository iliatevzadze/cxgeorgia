import { apiRequest } from "@/lib/api/client";

import type {
  Customer,
  CustomerCreateRequest,
  CustomerDeleteResponse,
  CustomerListFilters,
  CustomerUpdateRequest,
} from "./types";

export const customerPaths = {
  list: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/customers`,
  create: (workspaceId: string) =>
    `/api/v1/workspaces/${workspaceId}/customers`,
  detail: (workspaceId: string, customerId: string) =>
    `/api/v1/workspaces/${workspaceId}/customers/${customerId}`,
} as const;

export async function listCustomers(
  workspaceId: string,
  token: string,
  filters: CustomerListFilters = {},
): Promise<Customer[]> {
  const params = new URLSearchParams();
  if (filters.search?.trim()) {
    params.set("search", filters.search.trim());
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  const query = params.toString();
  const path = query
    ? `${customerPaths.list(workspaceId)}?${query}`
    : customerPaths.list(workspaceId);

  return apiRequest<Customer[]>(path, { token });
}

export async function getCustomer(
  workspaceId: string,
  customerId: string,
  token: string,
): Promise<Customer> {
  return apiRequest<Customer>(
    customerPaths.detail(workspaceId, customerId),
    { token },
  );
}

export async function createCustomer(
  workspaceId: string,
  payload: CustomerCreateRequest,
  token: string,
): Promise<Customer> {
  return apiRequest<Customer>(customerPaths.create(workspaceId), {
    method: "POST",
    body: payload,
    token,
  });
}

export async function updateCustomer(
  workspaceId: string,
  customerId: string,
  payload: CustomerUpdateRequest,
  token: string,
): Promise<Customer> {
  return apiRequest<Customer>(
    customerPaths.detail(workspaceId, customerId),
    {
      method: "PATCH",
      body: payload,
      token,
    },
  );
}

export async function deleteCustomer(
  workspaceId: string,
  customerId: string,
  token: string,
): Promise<CustomerDeleteResponse> {
  return apiRequest<CustomerDeleteResponse>(
    customerPaths.detail(workspaceId, customerId),
    {
      method: "DELETE",
      token,
    },
  );
}
