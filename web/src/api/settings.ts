import { api } from "./client";

export interface Setting {
  key: string;
  value_json: string;
  updated_at: string;
}

export interface SetupState {
  complete: boolean;
  step: string;
}

export const settingsApi = {
  list: () =>
    api.get<Setting[]>("/settings"),

  update: (key: string, value: string) =>
    api.put<Setting>(`/settings/${key}`, { value_json: value }),

  bulkUpdate: (settings: Record<string, string>) =>
    api.put<Setting[]>("/settings", { settings }),

  setupState: () =>
    api.get<SetupState>("/settings/setup/state"),
};