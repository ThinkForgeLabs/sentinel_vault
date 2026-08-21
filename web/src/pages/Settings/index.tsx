import { useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { cn } from "@/lib/cn";
import { GeneralSection } from "./GeneralSection";
import { StorageSection } from "./StorageSection";
import { AccountsSection } from "./AccountsSection";
import { AlertsSection } from "./AlertsSection";
import { CamerasSection } from "./CamerasSection";

const SECTIONS = [
  "General",
  "Storage",
  "Cameras",
  "Alerts",
  "Accounts",
  "Updates",
];

const WIDE_SECTIONS = new Set(["Accounts"]);

export default function SettingsPage() {
  const [section, setSection] = useState(0);

  const renderSection = () => {
    switch (SECTIONS[section]) {
      case "General":
        return <GeneralSection />;
      case "Storage":
        return <StorageSection />;
      case "Cameras":
        return <CamerasSection />;
      case "Alerts":
        return <AlertsSection />;
      case "Accounts":
        return <AccountsSection />;
      default:
        return (
          <p className="text-sm text-gray-500">
            {SECTIONS[section]} configuration will be available here.
          </p>
        );
    }
  };

  return (
    <>
      <Topbar title="Settings" />
      <div className="flex flex-1 overflow-hidden">
        {/* Settings nav */}
        <div className="hidden w-48 flex-shrink-0 border-r border-border bg-surface p-3 md:block overflow-y-auto">
          {SECTIONS.map((s, i) => (
            <button
              key={s}
              onClick={() => setSection(i)}
              className={cn(
                "block w-full rounded-lg px-3 py-2 text-left text-sm transition",
                section === i
                  ? "bg-accent/10 text-cyan-400 font-medium"
                  : "text-gray-400 hover:bg-hover hover:text-white"
              )}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Settings content */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div
            className={cn(
              "card animate-fade-in",
              WIDE_SECTIONS.has(SECTIONS[section]) ? "max-w-3xl" : "max-w-2xl"
            )}
          >
            <h3 className="mb-6 text-lg font-bold">{SECTIONS[section]}</h3>
            {renderSection()}
          </div>
        </div>
      </div>
    </>
  );
}
