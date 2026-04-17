import { EventCard } from "./EventCard";
import type { CameraEvent } from "@/types/event";

interface EventListProps {
  events: CameraEvent[];
  onSelect?: (event: CameraEvent) => void;
}

export function EventList({ events, onSelect }: EventListProps) {
  if (events.length === 0) {
    return (
      <div className="card py-16 text-center text-gray-500">
        No events match this filter.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {events.map((ev) => (
        <EventCard key={ev.id} event={ev} onClick={onSelect} />
      ))}
    </div>
  );
}