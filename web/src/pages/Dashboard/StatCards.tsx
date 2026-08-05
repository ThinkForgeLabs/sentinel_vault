import { Video, Zap, Bell, HardDrive } from "lucide-react";

interface Stat {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

interface StatCardsProps {
  camerasOnline: number;
  camerasTotal: number;
  eventsToday: number;
  alertsToday: number;
  recordingsCount: number;
}

export function StatCards({
  camerasOnline,
  camerasTotal,
  eventsToday,
  alertsToday,
  recordingsCount,
}: StatCardsProps) {
  const stats: Stat[] = [
    { label: "Cameras Online", value: `${camerasOnline}/${camerasTotal}`, icon: <Video size={22} />, color: "text-emerald-400" },
    { label: "Events Today", value: eventsToday, icon: <Zap size={22} />, color: "text-cyan-400" },
    { label: "Alerts Sent", value: alertsToday, icon: <Bell size={22} />, color: "text-amber-400" },
    { label: "Recordings", value: recordingsCount, icon: <HardDrive size={22} />, color: "text-violet-400" },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((s) => (
        <div key={s.label} className="card text-center">
          <div className={`mb-2 ${s.color}`}>{s.icon}</div>
          <div className="text-2xl font-extrabold leading-none">{s.value}</div>
          <div className="mt-1.5 text-xs text-gray-400">{s.label}</div>
        </div>
      ))}
    </div>
  );
}