export type UserStatus = "active" | "disabled";

export type User = {
  id: string;
  email: string;
  full_name: string | null;
  status: UserStatus;
  is_email_verified: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterInput = {
  email: string;
  password: string;
  full_name?: string | null;
};

export type LoginInput = {
  email: string;
  password: string;
};
