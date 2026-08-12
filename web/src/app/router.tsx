import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import LoginPage from "@/pages/Login";
import DashboardPage from "@/pages/Dashboard";
import CamerasPage from "@/pages/Cameras";
import WallPage from "@/pages/Wall";
import EventsPage from "@/pages/Events";
import PlaybackPage from "@/pages/Playback";
import SettingsPage from "@/pages/Settings";
import { useAuthStore } from "@/store/authStore";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "cameras", element: <CamerasPage /> },
      { path: "wall", element: <WallPage /> },
      { path: "events", element: <EventsPage /> },
      { path: "playback", element: <PlaybackPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);