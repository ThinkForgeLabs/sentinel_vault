import type { User } from "@/types/auth";

export interface SetupState {
  complete: boolean;
  step: string;
}

export interface SetupInitRequest {
  storage_path: string;
  admin_username: string;
  admin_display_name: string;
  admin_password: string;
  encryption_enabled: boolean;
}

export interface SetupCompleteResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
