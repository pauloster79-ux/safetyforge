import { ClipboardList } from 'lucide-react';

export function DailyLogOverviewPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
      <ClipboardList className="h-10 w-10 opacity-50" />
      <p className="text-sm font-medium">Daily Log Overview</p>
      <p className="text-xs">Today's log status across all projects coming soon.</p>
    </div>
  );
}
