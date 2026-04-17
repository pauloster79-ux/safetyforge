/**
 * useCanvasNavigate — drop-in replacement for react-router's useNavigate that
 * routes ROUTES paths into the canvas shell instead of React Router URL changes.
 *
 * Many pages were originally built for URL-based navigation but now render
 * inside the canvas pane. Replace:
 *   const navigate = useNavigate();
 * with:
 *   const navigate = useCanvasNavigate();
 * and broken navigate(ROUTES.XXX) calls start working without rewriting.
 *
 * The shim handles:
 *   - Path strings matching known ROUTES patterns → shell.openCanvas(...)
 *   - Numeric -1 (useNavigate(-1)) → shell.goBack()
 *   - Unknown paths → falls back to React Router's navigate for auth flows
 */

import { useCallback } from 'react';
import { useNavigate, type NavigateOptions } from 'react-router-dom';
import { useShell } from './useShell';

type NavigateArg = string | number | { to?: string };

interface RouteMatch {
  component: string;
  props: Record<string, unknown>;
  label: string;
}

/**
 * Parse a ROUTES path into canvas navigation parameters.
 * Returns null if the path is not canvas-navigable (e.g. /login, /dashboard).
 */
function matchRoute(path: string): RouteMatch | null {
  // Strip query string / hash
  const clean = path.split('?')[0].split('#')[0];

  // Exact matches
  const exact: Record<string, RouteMatch> = {
    '/projects': { component: 'ProjectListPage', props: {}, label: 'Projects' },
    '/projects/new': { component: 'ProjectCreatePage', props: {}, label: 'New Project' },
    '/documents': { component: 'DocumentListPage', props: {}, label: 'Documents' },
    '/documents/new': { component: 'DocumentCreatePage', props: {}, label: 'New Document' },
    '/workers': { component: 'WorkerListPage', props: {}, label: 'Workers' },
    '/workers/new': { component: 'WorkerCreatePage', props: {}, label: 'New Worker' },
    '/workers/certification-matrix': { component: 'CertificationMatrixPage', props: {}, label: 'Certifications' },
    '/equipment': { component: 'EquipmentPage', props: {}, label: 'Equipment' },
    '/equipment/new': { component: 'EquipmentCreatePage', props: {}, label: 'New Equipment' },
    '/osha-log': { component: 'OshaLogPage', props: {}, label: 'OSHA Log' },
    '/mock-inspection': { component: 'MockInspectionPage', props: {}, label: 'Mock Inspection' },
    '/analytics': { component: 'AnalyticsPage', props: {}, label: 'Analytics' },
    '/gc-portal': { component: 'GcPortalPage', props: {}, label: 'Compliance' },
    '/state-compliance': { component: 'StateCompliancePage', props: {}, label: 'State Compliance' },
    '/environmental': { component: 'EnvironmentalPage', props: {}, label: 'Environmental' },
    '/prequalification': { component: 'PrequalificationPage', props: {}, label: 'Prequalification' },
    '/settings': { component: 'CompanySettingsPage', props: {}, label: 'Settings' },
    '/billing': { component: 'BillingPage', props: {}, label: 'Billing' },
    '/team': { component: 'TeamMembersPage', props: {}, label: 'Team' },
    '/templates': { component: 'TemplatePickerPage', props: {}, label: 'Templates' },
    '/inspections': { component: 'InspectionListPage', props: {}, label: 'Inspections' },
    '/incidents': { component: 'IncidentListPage', props: {}, label: 'Incidents' },
  };
  if (clean in exact) return exact[clean];

  // Pattern matches
  let m: RegExpMatchArray | null;

  // /documents/:id
  m = clean.match(/^\/documents\/([^/]+)$/);
  if (m) return { component: 'DocumentEditPage', props: { documentId: m[1] }, label: 'Document' };

  // /workers/:id
  m = clean.match(/^\/workers\/([^/]+)$/);
  if (m) return { component: 'WorkerDetailPage', props: { workerId: m[1] }, label: 'Worker' };

  // /equipment/:id
  m = clean.match(/^\/equipment\/([^/]+)$/);
  if (m) return { component: 'EquipmentDetailPage', props: { equipmentId: m[1] }, label: 'Equipment' };

  // /projects/:id (but NOT /projects/new which was handled above)
  m = clean.match(/^\/projects\/([^/]+)$/);
  if (m) return { component: 'ProjectDetailPage', props: { projectId: m[1] }, label: 'Project' };

  // Project-scoped inspections
  m = clean.match(/^\/projects\/([^/]+)\/inspections\/new$/);
  if (m) return { component: 'InspectionCreatePage', props: { projectId: m[1] }, label: 'New Inspection' };
  m = clean.match(/^\/projects\/([^/]+)\/inspections\/([^/]+)$/);
  if (m) return { component: 'InspectionDetailPage', props: { projectId: m[1], inspectionId: m[2] }, label: 'Inspection' };

  // Toolbox talks
  m = clean.match(/^\/projects\/([^/]+)\/toolbox-talks\/new$/);
  if (m) return { component: 'ToolboxTalkCreatePage', props: { projectId: m[1] }, label: 'New Toolbox Talk' };
  m = clean.match(/^\/projects\/([^/]+)\/toolbox-talks\/([^/]+)\/deliver$/);
  if (m) return { component: 'ToolboxTalkDeliverPage', props: { projectId: m[1], talkId: m[2] }, label: 'Deliver Toolbox Talk' };
  m = clean.match(/^\/projects\/([^/]+)\/toolbox-talks\/([^/]+)$/);
  if (m) return { component: 'ToolboxTalkDetailPage', props: { projectId: m[1], talkId: m[2] }, label: 'Toolbox Talk' };

  // Hazards, morning brief, incidents
  m = clean.match(/^\/projects\/([^/]+)\/hazard-report\/new$/);
  if (m) return { component: 'HazardReportPage', props: { projectId: m[1] }, label: 'New Hazard Report' };
  m = clean.match(/^\/projects\/([^/]+)\/hazard-reports\/([^/]+)$/);
  if (m) return { component: 'HazardReportPage', props: { projectId: m[1], id: m[2] }, label: 'Hazard Report' };
  m = clean.match(/^\/projects\/([^/]+)\/morning-brief$/);
  if (m) return { component: 'MorningBriefPage', props: { projectId: m[1] }, label: 'Morning Brief' };
  m = clean.match(/^\/projects\/([^/]+)\/incidents\/new$/);
  if (m) return { component: 'IncidentCreatePage', props: { projectId: m[1] }, label: 'Report Incident' };
  m = clean.match(/^\/projects\/([^/]+)\/incidents\/([^/]+)$/);
  if (m) return { component: 'IncidentDetailPage', props: { projectId: m[1], incidentId: m[2] }, label: 'Incident' };

  // Daily logs
  m = clean.match(/^\/projects\/([^/]+)\/daily-logs\/new$/);
  if (m) return { component: 'DailyLogForm', props: { projectId: m[1] }, label: 'New Daily Log' };
  m = clean.match(/^\/projects\/([^/]+)\/daily-logs\/([^/]+)\/edit$/);
  if (m) return { component: 'DailyLogForm', props: { projectId: m[1], dailyLogId: m[2] }, label: 'Edit Daily Log' };
  m = clean.match(/^\/projects\/([^/]+)\/daily-logs\/([^/]+)$/);
  if (m) return { component: 'DailyLogDetailPage', props: { projectId: m[1], dailyLogId: m[2] }, label: 'Daily Log' };
  m = clean.match(/^\/projects\/([^/]+)\/daily-logs$/);
  if (m) return { component: 'DailyLogListPage', props: { projectId: m[1] }, label: 'Daily Logs' };

  return null;
}

export function useCanvasNavigate() {
  const shell = useShell();
  const routerNavigate = useNavigate();

  return useCallback(
    (to: NavigateArg, options?: NavigateOptions) => {
      // navigate(-1) = back
      if (typeof to === 'number') {
        if (to < 0) {
          shell.goBack();
          return;
        }
        return;
      }

      const path = typeof to === 'string' ? to : to.to ?? '';
      if (!path) return;

      const match = matchRoute(path);
      if (match) {
        shell.openCanvas(match);
        return;
      }

      // Fall back to React Router for unmapped paths (auth, onboarding, etc.)
      routerNavigate(path, options);
    },
    [shell, routerNavigate],
  );
}
