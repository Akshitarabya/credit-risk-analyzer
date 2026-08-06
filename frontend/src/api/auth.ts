import apiClient from "@/api/client";
import type { AuthToken, LoginPayload, RegisterPayload, User } from "@/types/auth";

export async function registerUser(payload: RegisterPayload): Promise<AuthToken> {
  const { data } = await apiClient.post<AuthToken>("/auth/register", payload);
  return data;
}

export async function loginUser(payload: LoginPayload): Promise<AuthToken> {
  const { data } = await apiClient.post<AuthToken>("/auth/login", payload);
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}
