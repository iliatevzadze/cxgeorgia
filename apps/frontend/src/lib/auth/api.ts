import { apiRequest } from "@/lib/api/client";

import type { LoginInput, RegisterInput, TokenResponse, User } from "./types";

export async function registerUser(input: RegisterInput): Promise<User> {
  return apiRequest<User>("/api/v1/auth/register", {
    method: "POST",
    body: {
      email: input.email.trim().toLowerCase(),
      password: input.password,
      full_name: input.full_name?.trim() || null,
    },
  });
}

export async function loginUser(input: LoginInput): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: {
      email: input.email.trim().toLowerCase(),
      password: input.password,
    },
  });
}

export async function getCurrentUser(token: string): Promise<User> {
  return apiRequest<User>("/api/v1/auth/me", {
    token,
  });
}
