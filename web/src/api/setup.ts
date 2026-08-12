import { api } from "./client";
import type { SetupCompleteResponse, SetupInitRequest, SetupState } from "@/types/setup";

export const setupApi = {
  state: () => api.get<SetupState>("/settings/setup/state"),

  init: (data: SetupInitRequest) =>
    api.post<SetupCompleteResponse>("/settings/setup/init", data),
};
