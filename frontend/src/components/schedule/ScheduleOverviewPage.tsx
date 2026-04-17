import { CalendarDays } from 'lucide-react';

export function ScheduleOverviewPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
      <CalendarDays className="h-10 w-10 opacity-50" />
      <p className="text-sm font-medium">Schedule Overview</p>
      <p className="text-xs">Cross-project schedule view coming soon.</p>
    </div>
  );
}
