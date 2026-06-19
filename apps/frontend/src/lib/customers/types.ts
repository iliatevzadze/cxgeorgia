export type CustomerStatus = "active" | "archived";

export type Customer = {
  id: string;
  workspace_id: string;
  display_name: string;
  email: string | null;
  phone: string | null;
  external_id: string | null;
  locale: string | null;
  notes: string | null;
  status: CustomerStatus;
  created_at: string;
  updated_at: string;
};

export type CustomerCreateRequest = {
  display_name: string;
  email?: string;
  phone?: string;
  external_id?: string;
  locale?: string;
  notes?: string;
  status?: CustomerStatus;
};

export type CustomerUpdateRequest = {
  display_name?: string;
  email?: string | null;
  phone?: string | null;
  external_id?: string | null;
  locale?: string | null;
  notes?: string | null;
  status?: CustomerStatus;
};

export type CustomerDeleteResponse = {
  id: string;
  deleted: boolean;
};

export type CustomerListFilters = {
  search?: string;
  status?: CustomerStatus;
};
