import React from "react";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  // Add context providers here as needed (theme, query client, etc.)
  return <>{children}</>;
}