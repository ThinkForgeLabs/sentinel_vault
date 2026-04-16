import { useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/cn";

const SECTIONS = [
  "General",
  "Storage",
  "Cameras",
  "AI & Models",
  "Privacy",
  "Accounts",
  "Updates",
];

export default function SettingsPage() {
  const [section, setSection] = useState(0);

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
          <div className="card max-w-2xl animate-fade-in">
            <h3 className="mb-6 text-lg font-bold">{SECTIONS[section]}</h3>

            {section === 0 && (
              <div className="space-y-4">
                <Input label="System Name" defaultValue="Sentinel Vault Home" />
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                    Time Zone
                  </label>
                  <select className="w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent">
                    <option>America/New_York (UTC-4)</option>
                    <option>America/Chicago (UTC-5)</option>
                    <option>Europe/London (UTC+1)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                    Theme
                  </label>
                  <div className="flex gap-2">
                    {["Dark", "Light", "Auto"].map((t) => (
                      <button
                        key={t}
                        className={cn(
                          "rounded-full border px-3.5 py-1.5 text-xs font-medium transition",
                          t === "Dark"
                            ? "border-cyan-400 bg-accent/10 text-cyan-400"
                            : "border-border text-gray-400 hover:text-white"
                        )}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="pt-2">
                  <Button>Save Changes</Button>
                </div>
              </div>
            )}

            {section === 1 && (
              <div className="space-y-4">
                <Input
                  label="Storage Path"
                  defaultValue="/data/sentinel-vault/recordings"
                />
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                    Storage Usage
                  </label>
                  <div className="h-3 rounded-full bg-gray-700 overflow-hidden mb-1">
                    <div className="h-full w-1/4 rounded-full bg-cyan-400" />
                  </div>
                  <p className="text-xs text-gray-500">142 GB used of 500 GB</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                    Default Retention
                  </label>
                  <select className="w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none">
                    <option>7 days</option>
                    <option selected>14 days</option>
                    <option>30 days</option>
                    <option>60 days</option>
                  </select>
                </div>
                <div className="pt-2">
                  <Button>Save Changes</Button>
                </div>
              </div>
            )}

            {section > 1 && (
              <p className="text-sm text-gray-500">
                {SECTIONS[section]} configuration will be available here.
              </p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}