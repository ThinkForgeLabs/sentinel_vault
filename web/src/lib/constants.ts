export const API_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

export const EVENT_TYPES = ["motion", "camera_offline"] as const;

export const IMPORTANCE_LEVELS = ["low", "medium", "high", "critical"] as const;

export const NAV_ITEMS = [
  { id: "dashboard", label: "Home", icon: "Home", path: "/" },
  { id: "cameras", label: "Cameras", icon: "Video", path: "/cameras" },
  { id: "events", label: "Events", icon: "Zap", path: "/events" },
  { id: "playback", label: "Playback", icon: "Clock", path: "/playback" },
  { id: "settings", label: "Settings", icon: "Settings", path: "/settings" },
] as const;