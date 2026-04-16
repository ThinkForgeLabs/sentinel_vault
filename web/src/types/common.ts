export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  request_id?: string;
}

export type Status = "online" | "offline" | "recording" | "error";
export type Importance = "low" | "medium" | "high" | "critical";
export type ReviewStatus = "pending" | "reviewed" | "dismissed";