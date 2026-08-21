import { api } from "./client";
import type { User } from "@/types/auth";

export interface UserCreate {
  username: string;
  display_name: string;
  password: string;
  role?: "owner" | "viewer";
}

export interface UserUpdate {
  display_name?: string;
  role?: "owner" | "viewer";
  is_active?: boolean;
}

export interface SelfUpdate {
  display_name?: string;
  current_password?: string;
  new_password?: string;
}

export const usersApi = {
  list: () => api.get<User[]>("/users"),

  create: (data: UserCreate) => api.post<User>("/users", data),

  update: (id: string, data: UserUpdate) => api.put<User>(`/users/${id}`, data),

  delete: (id: string) => api.delete(`/users/${id}`),

  updateSelf: (data: SelfUpdate) => api.put<User>("/users/me", data),
};
