import { api } from "./client";
import type { LoginRequest, TokenResponse, User } from "@/types/auth";

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<TokenResponse>("/auth/login", data),

  refresh: (refreshToken: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken }),

  me: () =>
    api.get<User>("/auth/me"),
};