// src/api/storage.ts
import { api } from "./client";
import type {
  StorageStats,
  StorageSettingsPayload,
  CleanupResult,
} from "@/types/storage";

export const storageApi = {
  /** GET /recordings/storage */
  stats: () =>
    api.get<StorageStats>("/recordings/storage"),

  /** GET /recordings/storage/settings */
  getSettings: () =>
    api.get<StorageSettingsPayload>("/recordings/storage/settings"),

  /** PUT /recordings/storage/settings */
  updateSettings: (payload: StorageSettingsPayload) =>
    api.put<StorageSettingsPayload>("/recordings/storage/settings", payload),

  /** POST /recordings/storage/cleanup */
  cleanup: () =>
    api.post<CleanupResult>("/recordings/storage/cleanup"),
};