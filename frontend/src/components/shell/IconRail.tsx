/**
 * Icon rail — vertical strip on desktop/tablet, bottom nav on mobile.
 *
 * Icons: Chat, Projects, Schedule, Daily Logs, Workers, Equipment,
 *        Safety, Documents, Reports, Settings.
 * Clicking opens canvas list views or focuses chat with context.
 */

import {
  MessageSquare,
  FolderKanban,
  CalendarDays,
  ClipboardList,
  Users,
  Wrench,
  ShieldCheck,
  FileText,
  BarChart3,
  BookOpen,
  Database,
  Settings,
  MoreHorizontal,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useShell, type RailItem } from '@/hooks/useShell';

interface RailEntry {
  id: RailItem;
  icon: typeof MessageSquare;
  label: string;
  /** If set, clicking opens this canvas component instead of focusing chat */
  canvasComponent?: string;
  canvasLabel?: string;
}

const RAIL_ITEMS: RailEntry[] = [
  { id: 'chat', icon: MessageSquare, label: 'Chat' },
  { id: 'projects', icon: FolderKanban, label: 'Projects', canvasComponent: 'ProjectListPage', canvasLabel: 'Projects' },
  { id: 'schedule', icon: CalendarDays, label: 'Schedule', canvasComponent: 'ScheduleOverviewPage', canvasLabel: 'Schedule' },
  { id: 'daily-logs', icon: ClipboardList, label: 'Daily Logs', canvasComponent: 'DailyLogOverviewPage', canvasLabel: 'Daily Logs' },
  { id: 'workers', icon: Users, label: 'Workers', canvasComponent: 'WorkerListPage', canvasLabel: 'Workers' },
  { id: 'equipment', icon: Wrench, label: 'Equipment', canvasComponent: 'EquipmentPage', canvasLabel: 'Equipment' },
  { id: 'safety', icon: ShieldCheck, label: 'Safety', canvasComponent: 'SafetyOverviewPage', canvasLabel: 'Safety' },
  { id: 'documents', icon: FileText, label: 'Documents', canvasComponent: 'DocumentListPage', canvasLabel: 'Documents' },
  { id: 'reports', icon: BarChart3, label: 'Reports', canvasComponent: 'AnalyticsPage', canvasLabel: 'Analytics' },
  { id: 'queries', icon: Database, label: 'Queries', canvasComponent: 'QueryCanvasPage', canvasLabel: 'Query Canvas' },
  { id: 'knowledge', icon: BookOpen, label: 'Knowledge', canvasComponent: 'KnowledgePage', canvasLabel: 'My Knowledge' },
  { id: 'settings', icon: Settings, label: 'Settings', canvasComponent: 'CompanySettingsPage', canvasLabel: 'Settings' },
];

/** Desktop/tablet items */
const DESKTOP_ITEMS = RAIL_ITEMS;

/** Mobile bottom nav (first 4 + More) */
const MOBILE_ITEMS = RAIL_ITEMS.slice(0, 4);

export function IconRail() {
  const { activeRail, setActiveRail, breakpoint, openCanvas, closeCanvas, setMobilePane } = useShell();

  const handleClick = (entry: RailEntry) => {
    setActiveRail(entry.id);
    if (entry.id === 'chat') {
      closeCanvas();
      if (breakpoint === 'mobile') setMobilePane('chat');
    } else if (entry.canvasComponent) {
      openCanvas({
        component: entry.canvasComponent,
        props: {},
        label: entry.canvasLabel || entry.label,
      });
    }
  };

  // ── Mobile: bottom nav bar ──
  if (breakpoint === 'mobile') {
    return (
      <nav className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-border bg-white px-1 py-1.5 safe-area-pb">
        {MOBILE_ITEMS.map((entry) => {
          const active = activeRail === entry.id;
          return (
            <button
              key={entry.id}
              onClick={() => handleClick(entry)}
              className={cn(
                'flex flex-col items-center gap-0.5 rounded-sm px-3 py-1 text-[10px] font-medium transition-colors',
                active
                  ? 'text-foreground'
                  : 'text-muted-foreground',
              )}
            >
              <entry.icon className={cn('h-5 w-5', active && 'text-machine-dark')} />
              <span>{entry.label}</span>
              {active && (
                <div className="h-0.5 w-4 rounded-full bg-machine" />
              )}
            </button>
          );
        })}
        {/* More button for remaining items */}
        <button
          className="flex flex-col items-center gap-0.5 rounded-sm px-3 py-1 text-[10px] font-medium text-muted-foreground"
          onClick={() => {
            setActiveRail('reports');
            openCanvas({ component: 'AnalyticsPage', props: {}, label: 'Analytics' });
          }}
        >
          <MoreHorizontal className="h-5 w-5" />
          <span>More</span>
        </button>
      </nav>
    );
  }

  // ── Desktop/Tablet: vertical icon rail ──
  return (
    <nav className="flex h-full w-12 flex-col items-center border-r border-border bg-white py-3">
      {/* Logo */}
      <div className="mb-4 flex h-8 w-8 items-center justify-center rounded-md bg-machine">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>

      {/* Rail items */}
      <div className="flex flex-1 flex-col items-center gap-1">
        {DESKTOP_ITEMS.map((entry) => {
          const active = activeRail === entry.id;
          return (
            <button
              key={entry.id}
              onClick={() => handleClick(entry)}
              title={entry.label}
              className={cn(
                'group relative flex h-10 w-10 items-center justify-center rounded-sm transition-colors',
                active
                  ? 'bg-machine-wash text-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )}
            >
              <entry.icon className={cn('h-[18px] w-[18px]', active && 'text-machine-dark')} />
              {active && (
                <div className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r-full bg-machine" />
              )}
              {/* Tooltip */}
              <span className="pointer-events-none absolute left-full ml-2 whitespace-nowrap rounded bg-foreground px-2 py-1 font-mono text-[10px] text-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100">
                {entry.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
