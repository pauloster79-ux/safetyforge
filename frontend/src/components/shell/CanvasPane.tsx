/**
 * CanvasPane — detail view container for the conversational-first layout.
 *
 * Renders existing page components inside a constrained container.
 * Has its own header with back button, breadcrumb, and close button.
 * Navigation is driven by clicking cards in chat or rail items.
 */

import { lazy, Suspense } from 'react';
import { ArrowLeft, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useShell, type CanvasView } from '@/hooks/useShell';

// ---------------------------------------------------------------------------
// Lazy-loaded page components (reuse existing pages as-is)
// ---------------------------------------------------------------------------

const PAGE_COMPONENTS: Record<string, React.LazyExoticComponent<React.ComponentType<any>>> = {
  DashboardPage: lazy(() => import('@/components/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage }))),
  ProjectListPage: lazy(() => import('@/components/projects/ProjectListPage').then((m) => ({ default: m.ProjectListPage }))),
  ProjectCreatePage: lazy(() => import('@/components/projects/ProjectCreatePage').then((m) => ({ default: m.ProjectCreatePage }))),
  ProjectDetailPage: lazy(() => import('@/components/projects/ProjectDetailPage').then((m) => ({ default: m.ProjectDetailPage }))),
  InspectionListPage: lazy(() => import('@/components/inspections/InspectionListPage').then((m) => ({ default: m.InspectionListPage }))),
  InspectionCreatePage: lazy(() => import('@/components/inspections/InspectionCreatePage').then((m) => ({ default: m.InspectionCreatePage }))),
  InspectionDetailPage: lazy(() => import('@/components/inspections/InspectionDetailPage').then((m) => ({ default: m.InspectionDetailPage }))),
  WorkerListPage: lazy(() => import('@/components/workers/WorkerListPage').then((m) => ({ default: m.WorkerListPage }))),
  WorkerCreatePage: lazy(() => import('@/components/workers/WorkerCreatePage').then((m) => ({ default: m.WorkerCreatePage }))),
  WorkerDetailPage: lazy(() => import('@/components/workers/WorkerDetailPage').then((m) => ({ default: m.WorkerDetailPage }))),
  CertificationMatrixPage: lazy(() => import('@/components/workers/CertificationMatrixPage').then((m) => ({ default: m.CertificationMatrixPage }))),
  DocumentListPage: lazy(() => import('@/components/documents/DocumentListPage').then((m) => ({ default: m.DocumentListPage }))),
  DocumentCreatePage: lazy(() => import('@/components/documents/DocumentCreatePage').then((m) => ({ default: m.DocumentCreatePage }))),
  DocumentEditPage: lazy(() => import('@/components/documents/DocumentEditPage').then((m) => ({ default: m.DocumentEditPage }))),
  TemplatePickerPage: lazy(() => import('@/components/templates/TemplatePickerPage').then((m) => ({ default: m.TemplatePickerPage }))),
  CompanySettingsPage: lazy(() => import('@/components/company/CompanySettingsPage').then((m) => ({ default: m.CompanySettingsPage }))),
  BillingPage: lazy(() => import('@/components/billing/BillingPage').then((m) => ({ default: m.BillingPage }))),
  ToolboxTalkListPage: lazy(() => import('@/components/toolbox-talks/ToolboxTalkListPage').then((m) => ({ default: m.ToolboxTalkListPage }))),
  ToolboxTalkDetailPage: lazy(() => import('@/components/toolbox-talks/ToolboxTalkDetailPage').then((m) => ({ default: m.ToolboxTalkDetailPage }))),
  ToolboxTalkCreatePage: lazy(() => import('@/components/toolbox-talks/ToolboxTalkCreatePage').then((m) => ({ default: m.ToolboxTalkCreatePage }))),
  ToolboxTalkDeliverPage: lazy(() => import('@/components/toolbox-talks/ToolboxTalkDeliverPage').then((m) => ({ default: m.ToolboxTalkDeliverPage }))),
  IncidentListPage: lazy(() => import('@/components/incidents/IncidentListPage').then((m) => ({ default: m.IncidentListPage }))),
  IncidentDetailPage: lazy(() => import('@/components/incidents/IncidentDetailPage').then((m) => ({ default: m.IncidentDetailPage }))),
  IncidentCreatePage: lazy(() => import('@/components/incidents/IncidentCreatePage').then((m) => ({ default: m.IncidentCreatePage }))),
  DailyLogListPage: lazy(() => import('@/components/daily-logs/DailyLogListPage').then((m) => ({ default: m.DailyLogListPage }))),
  DailyLogDetailPage: lazy(() => import('@/components/daily-logs/DailyLogDetailPage').then((m) => ({ default: m.DailyLogDetailPage }))),
  VoiceInspectionPage: lazy(() => import('@/components/voice-inspection/VoiceInspectionPage')),
  OshaLogPage: lazy(() => import('@/components/osha-log/OshaLogPage').then((m) => ({ default: m.OshaLogPage }))),
  MockInspectionPage: lazy(() => import('@/components/mock-inspection/MockInspectionPage').then((m) => ({ default: m.MockInspectionPage }))),
  HazardReportPage: lazy(() => import('@/components/hazards/HazardReportPage').then((m) => ({ default: m.HazardReportPage }))),
  MorningBriefPage: lazy(() => import('@/components/morning-brief/MorningBriefPage').then((m) => ({ default: m.MorningBriefPage }))),
  AnalyticsPage: lazy(() => import('@/components/analytics/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage }))),
  PrequalificationPage: lazy(() => import('@/components/prequalification/PrequalificationPage').then((m) => ({ default: m.PrequalificationPage }))),
  GcPortalPage: lazy(() => import('@/components/gc-portal/GcPortalPage').then((m) => ({ default: m.GcPortalPage }))),
  StateCompliancePage: lazy(() => import('@/components/state-compliance/StateCompliancePage').then((m) => ({ default: m.StateCompliancePage }))),
  EnvironmentalPage: lazy(() => import('@/components/environmental/EnvironmentalPage').then((m) => ({ default: m.EnvironmentalPage }))),
  EquipmentPage: lazy(() => import('@/components/equipment/EquipmentPage').then((m) => ({ default: m.EquipmentPage }))),
  EquipmentCreatePage: lazy(() => import('@/components/equipment/EquipmentCreatePage').then((m) => ({ default: m.EquipmentCreatePage }))),
  EquipmentDetailPage: lazy(() => import('@/components/equipment/EquipmentDetailPage').then((m) => ({ default: m.EquipmentDetailPage }))),
  DailyLogForm: lazy(() => import('@/components/daily-logs/DailyLogForm').then((m) => ({ default: m.DailyLogForm }))),
  TeamMembersPage: lazy(() => import('@/components/team/TeamMembersPage').then((m) => ({ default: m.TeamMembersPage }))),
  ScheduleOverviewPage: lazy(() => import('@/components/schedule/ScheduleOverviewPage').then((m) => ({ default: m.ScheduleOverviewPage }))),
  DailyLogOverviewPage: lazy(() => import('@/components/daily-logs/DailyLogOverviewPage').then((m) => ({ default: m.DailyLogOverviewPage }))),
  SafetyOverviewPage: lazy(() => import('@/components/safety/SafetyOverviewPage').then((m) => ({ default: m.SafetyOverviewPage }))),
  KnowledgePage: lazy(() => import('@/components/knowledge/KnowledgePage').then((m) => ({ default: m.KnowledgePage }))),
  ConversationKnowledgePage: lazy(() => import('@/components/knowledge/ConversationKnowledgePage').then((m) => ({ default: m.ConversationKnowledgePage }))),
  QueryCanvasPage: lazy(() => import('@/components/queries/QueryCanvasPage').then((m) => ({ default: m.QueryCanvasPage }))),
};

// ---------------------------------------------------------------------------
// Loading fallback
// ---------------------------------------------------------------------------

function CanvasLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Canvas content renderer
// ---------------------------------------------------------------------------

function CanvasContent({ view }: { view: CanvasView }) {
  const Component = PAGE_COMPONENTS[view.component];

  if (!Component) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
        <p className="text-sm">Page not found: {view.component}</p>
      </div>
    );
  }

  return (
    <Suspense fallback={<CanvasLoading />}>
      <Component {...view.props} />
    </Suspense>
  );
}

// ---------------------------------------------------------------------------
// History stack for back navigation within canvas
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// CanvasPane
// ---------------------------------------------------------------------------

export function CanvasPane() {
  const { canvasView, canvasOpen, closeCanvas, goBack, canGoBack, breakpoint } = useShell();

  if (!canvasOpen || !canvasView) return null;

  // On mobile, render as full-screen overlay
  const isMobileOverlay = breakpoint === 'mobile';

  return (
    <div
      className={
        isMobileOverlay
          ? 'fixed inset-0 z-50 flex flex-col bg-background'
          : 'flex h-full flex-1 flex-col border-l border-border bg-background'
      }
    >
      {/* Canvas header */}
      <div className="flex items-center justify-between border-b border-border bg-card px-4 py-2.5">
        <div className="flex items-center gap-2 min-w-0">
          {(canGoBack || isMobileOverlay) && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0"
              onClick={canGoBack ? goBack : closeCanvas}
              title={canGoBack ? 'Back' : 'Close'}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
          )}
          <span className="truncate text-[12px] font-semibold">{canvasView.label}</span>
        </div>
        {!isMobileOverlay && (
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closeCanvas}>
            <X className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>

      {/* Canvas content */}
      <div className="flex-1 overflow-y-auto p-4">
        <CanvasContent view={canvasView} />
      </div>
    </div>
  );
}
