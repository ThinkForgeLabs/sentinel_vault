import { useEffect, useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EventFiltersBar } from "./EventFilters";
import { EventList } from "./EventList";
import { eventsApi } from "@/api/events";
import type { CameraEvent } from "@/types/event";

export default function EventsPage() {
  const [events, setEvents] = useState<CameraEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    async function load() {
      try {
        const type = filter === "all" ? undefined : `${filter}_detected`;
        const data = await eventsApi.list({ event_type: type });
        setEvents(data);
      } catch {
        // empty in dev
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filter]);

  return (
    <>
      <Topbar title="Events" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <PageHeader title="Events" description="AI-detected events from all cameras" />
        <div className="mb-5">
          <EventFiltersBar active={filter} onChange={setFilter} />
        </div>
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="animate-fade-in">
            <EventList events={events} />
          </div>
        )}
      </div>
    </>
  );
}