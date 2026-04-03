# SafetyForge Frontend Architecture

*Last updated: 2026-03-31*

This document is the definitive frontend architecture blueprint for SafetyForge. Every component, route, type, and pattern defined here traces back to the product strategy and vision. Engineers build from this document; deviations require an ADR.

---

## 1. APPLICATION STRUCTURE

The current codebase is a flat structure with components organized by page. This plan restructures into a feature-sliced architecture that scales across all four product phases while preserving the existing code.

```
src/
├── app/                          # App shell
│   ├── App.tsx                   # Root component with router
│   ├── main.tsx                  # Entry point, providers
│   ├── providers/
│   │   ├── AuthProvider.tsx      # Firebase auth context
│   │   ├── ProjectProvider.tsx   # Current project context
│   │   ├── I18nProvider.tsx      # Internationalization context
│   │   └── OfflineProvider.tsx   # Connectivity + sync context
│   └── router.tsx                # Centralized route definitions
│
├── lib/                          # Shared utilities (no UI)
│   ├── api/
│   │   ├── client.ts             # Base HTTP client (refactored from api.ts)
│   │   ├── interceptors.ts       # Auth, error, offline interceptors
│   │   ├── offline-queue.ts      # Queued mutations for offline
│   │   ├── file-upload.ts        # Multipart upload for photos/voice
│   │   └── resources/            # Resource-specific API modules
│   │       ├── documents.api.ts
│   │       ├── projects.api.ts
│   │       ├── inspections.api.ts
│   │       ├── toolbox-talks.api.ts
│   │       ├── hazards.api.ts
│   │       ├── incidents.api.ts
│   │       ├── workers.api.ts
│   │       ├── equipment.api.ts
│   │       ├── training.api.ts
│   │       ├── mock-inspection.api.ts
│   │       ├── morning-brief.api.ts
│   │       ├── analytics.api.ts
│   │       ├── prequalification.api.ts
│   │       ├── company.api.ts
│   │       └── billing.api.ts
│   ├── constants.ts              # App-wide constants, enums
│   ├── utils.ts                  # cn(), formatters, validators
│   ├── firebase.ts               # Firebase config (existing)
│   ├── demo-data.ts              # Demo mode data (existing)
│   ├── date.ts                   # Date formatting (locale-aware)
│   ├── currency.ts               # Dollar formatting
│   ├── geolocation.ts            # GPS utilities
│   └── speech.ts                 # Web Speech API wrapper
│
├── types/                        # Global TypeScript types
│   ├── models.ts                 # All domain models (Section 4)
│   ├── api.ts                    # API request/response envelopes
│   ├── forms.ts                  # Form field definitions
│   └── i18n.ts                   # Translation key types
│
├── hooks/                        # Shared hooks
│   ├── useAuth.ts                # Auth context hook (existing)
│   ├── useCurrentProject.ts      # Current project from context
│   ├── useOffline.ts             # Connectivity state
│   ├── useCamera.ts              # Camera capture
│   ├── useVoiceInput.ts          # Voice recording + transcription
│   ├── useGeolocation.ts         # GPS coordinates
│   ├── useDebounce.ts            # Input debounce
│   ├── useMediaQuery.ts          # Responsive breakpoints
│   └── useLocale.ts              # Current language
│
├── components/
│   ├── ui/                       # shadcn/ui primitives (existing)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── textarea.tsx
│   │   ├── badge.tsx
│   │   ├── separator.tsx
│   │   ├── sonner.tsx
│   │   └── ... (all shadcn components)
│   │
│   ├── shared/                   # Shared business components
│   │   ├── DataTable.tsx          # Filterable, sortable, paginated table
│   │   ├── FormBuilder.tsx        # Dynamic form renderer from field defs
│   │   ├── PhotoCapture.tsx       # Camera + upload + preview
│   │   ├── VoiceInput.tsx         # Record + transcribe + display
│   │   ├── SignatureCapture.tsx   # Touch signature pad
│   │   ├── ComplianceScoreCard.tsx # Score ring with color coding
│   │   ├── RiskBadge.tsx          # Color-coded risk level pill
│   │   ├── TimelineView.tsx       # Chronological event timeline
│   │   ├── DocumentViewer.tsx     # Section-by-section viewer/editor
│   │   ├── StatusIndicator.tsx    # Green/yellow/red dot
│   │   ├── EmptyState.tsx         # Consistent empty states
│   │   ├── LoadingSkeleton.tsx    # Consistent loading skeletons
│   │   ├── OfflineBanner.tsx      # "You are offline" indicator
│   │   ├── LanguageToggle.tsx     # EN/ES switch
│   │   ├── FileAttachment.tsx     # File upload with preview
│   │   ├── OshaReference.tsx      # Styled OSHA citation display
│   │   └── ConfirmDialog.tsx      # Reusable confirmation modal
│   │
│   ├── layout/                   # App chrome
│   │   ├── AppLayout.tsx          # Shell with sidebar + header + outlet
│   │   ├── Sidebar.tsx            # Navigation sidebar (collapsible)
│   │   ├── Header.tsx             # Top bar with user menu, project picker
│   │   ├── MobileNav.tsx          # Bottom tab bar for mobile
│   │   ├── ProjectPicker.tsx      # Dropdown to switch active project
│   │   └── BreadcrumbNav.tsx      # Contextual breadcrumbs
│   │
│   ├── auth/                     # Authentication
│   │   ├── LoginPage.tsx
│   │   ├── SignUpPage.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── PublicRoute.tsx
│   │   └── OnboardingWizard.tsx   # NEW: Company setup after signup
│   │
│   ├── landing/                  # Public marketing
│   │   ├── LandingPage.tsx
│   │   ├── PricingSection.tsx
│   │   ├── FeaturesSection.tsx
│   │   ├── TestimonialsSection.tsx
│   │   └── RoiCalculator.tsx      # NEW: Interactive savings calculator
│   │
│   ├── blog/                     # Content marketing
│   │   ├── BlogListPage.tsx
│   │   ├── BlogPostPage.tsx
│   │   └── BlogSidebar.tsx
│   │
│   ├── dashboard/                # Main dashboard
│   │   ├── DashboardPage.tsx      # Refactored: project-aware overview
│   │   ├── ComplianceOverview.tsx  # Multi-project red/yellow/green
│   │   ├── QuickActions.tsx        # Field-first action cards
│   │   ├── UpcomingDeadlines.tsx   # Cert expirations, submissions
│   │   ├── RecentActivity.tsx      # Activity feed across projects
│   │   └── UsageCard.tsx           # Subscription usage
│   │
│   ├── projects/                 # Project management
│   │   ├── ProjectListPage.tsx
│   │   ├── ProjectCreatePage.tsx
│   │   ├── ProjectDetailPage.tsx   # Project hub with tabs
│   │   ├── ProjectSettingsPage.tsx
│   │   └── ProjectComplianceCard.tsx
│   │
│   ├── documents/                # Document generation & editing
│   │   ├── DocumentListPage.tsx    # Existing, add project filter
│   │   ├── DocumentCreatePage.tsx  # Existing wizard
│   │   ├── DocumentEditPage.tsx    # Existing section editor
│   │   └── DocumentExportDialog.tsx # PDF/Word export options
│   │
│   ├── inspections/              # Daily inspection logs
│   │   ├── InspectionListPage.tsx
│   │   ├── InspectionCreatePage.tsx # Mobile-optimized checklist
│   │   ├── InspectionDetailPage.tsx
│   │   └── InspectionChecklist.tsx  # Checklist renderer with photo attach
│   │
│   ├── toolbox-talks/            # Toolbox talk delivery
│   │   ├── ToolboxTalkListPage.tsx
│   │   ├── ToolboxTalkDeliverPage.tsx # Full-screen delivery mode
│   │   ├── ToolboxTalkDetailPage.tsx
│   │   ├── ToolboxTalkSignOff.tsx    # Crew signature collection
│   │   └── ToolboxTalkViewer.tsx     # Bilingual display
│   │
│   ├── hazards/                  # Hazard reporting
│   │   ├── HazardListPage.tsx
│   │   ├── HazardReportPage.tsx     # Photo + voice + AI analysis
│   │   ├── HazardDetailPage.tsx
│   │   └── HazardAnalysisCard.tsx   # AI hazard assessment display
│   │
│   ├── incidents/                # Incident management
│   │   ├── IncidentListPage.tsx
│   │   ├── IncidentReportPage.tsx    # Voice-first incident capture
│   │   ├── IncidentDetailPage.tsx
│   │   ├── IncidentTimeline.tsx      # Investigation timeline
│   │   └── RootCauseAnalysis.tsx     # 5-Why / fishbone guided flow
│   │
│   ├── workers/                  # Worker management
│   │   ├── WorkerListPage.tsx
│   │   ├── WorkerDetailPage.tsx
│   │   ├── WorkerCreatePage.tsx
│   │   ├── CertificationCard.tsx     # Single cert with expiry status
│   │   └── TrainingMatrix.tsx        # Grid of workers x certifications
│   │
│   ├── equipment/                # Equipment inspection
│   │   ├── EquipmentListPage.tsx
│   │   ├── EquipmentDetailPage.tsx
│   │   ├── EquipmentInspectionPage.tsx # Daily checklist for equipment
│   │   └── EquipmentCreatePage.tsx
│   │
│   ├── mock-inspection/          # Mock OSHA inspection
│   │   ├── MockInspectionPage.tsx    # Run inspection flow
│   │   ├── MockInspectionResults.tsx # Citation-format findings
│   │   ├── MockInspectionHistory.tsx
│   │   └── FindingCard.tsx           # Individual finding display
│   │
│   ├── morning-brief/            # Morning safety brief
│   │   ├── MorningBriefPage.tsx      # Today's brief
│   │   ├── RiskScoreDisplay.tsx      # Visual risk score ring
│   │   ├── BriefActionItems.tsx      # Actionable items list
│   │   └── MorningBriefHistory.tsx
│   │
│   ├── training/                 # Training & certification tracker
│   │   ├── TrainingDashboard.tsx
│   │   ├── CertificationTracker.tsx
│   │   ├── TrainingRecordPage.tsx
│   │   └── ExpirationAlerts.tsx
│   │
│   ├── prequalification/         # ISN/Avetta automation (Phase 3)
│   │   ├── PrequalDashboard.tsx
│   │   ├── PrequalSubmissionPage.tsx
│   │   └── PrequalGapAnalysis.tsx
│   │
│   ├── analytics/                # Safety analytics
│   │   ├── AnalyticsDashboard.tsx
│   │   ├── EmrModelingPage.tsx       # EMR impact calculator
│   │   ├── TrendCharts.tsx
│   │   ├── Osha300Page.tsx           # OSHA 300 log management
│   │   └── ComplianceScoreTrend.tsx
│   │
│   ├── settings/                 # Company settings
│   │   ├── CompanySettingsPage.tsx    # Existing
│   │   ├── UserManagementPage.tsx
│   │   ├── NotificationSettings.tsx
│   │   └── IntegrationSettings.tsx
│   │
│   └── billing/                  # Subscription management
│       ├── BillingPage.tsx           # Existing
│       ├── PlanSelector.tsx
│       └── InvoiceHistory.tsx
│
├── features/                     # Feature-specific non-UI logic
│   ├── documents/
│   │   ├── useDocuments.ts           # Existing, refactored
│   │   ├── useDocumentExport.ts
│   │   └── document.utils.ts
│   ├── inspections/
│   │   ├── useInspections.ts
│   │   ├── useInspectionChecklist.ts
│   │   └── inspection.utils.ts
│   ├── toolbox-talks/
│   │   ├── useToolboxTalks.ts
│   │   └── useToolboxTalkDelivery.ts
│   ├── hazards/
│   │   ├── useHazards.ts
│   │   └── useHazardAnalysis.ts
│   ├── incidents/
│   │   ├── useIncidents.ts
│   │   └── useRootCauseAnalysis.ts
│   ├── workers/
│   │   ├── useWorkers.ts
│   │   └── useCertifications.ts
│   ├── equipment/
│   │   ├── useEquipment.ts
│   │   └── useEquipmentInspections.ts
│   ├── mock-inspection/
│   │   └── useMockInspection.ts
│   ├── morning-brief/
│   │   └── useMorningBrief.ts
│   ├── training/
│   │   └── useTraining.ts
│   ├── analytics/
│   │   ├── useAnalytics.ts
│   │   └── useEmrModeling.ts
│   ├── projects/
│   │   └── useProjects.ts
│   └── company/
│       ├── useCompany.ts             # Existing
│       └── useSubscription.ts
│
├── i18n/                         # Internationalization
│   ├── index.ts                  # i18n setup
│   ├── useTranslation.ts         # Translation hook
│   ├── locales/
│   │   ├── en/
│   │   │   ├── common.json
│   │   │   ├── dashboard.json
│   │   │   ├── inspections.json
│   │   │   ├── toolbox-talks.json
│   │   │   ├── hazards.json
│   │   │   ├── incidents.json
│   │   │   ├── workers.json
│   │   │   └── ... (one file per feature)
│   │   └── es/
│   │       ├── common.json
│   │       ├── dashboard.json
│   │       ├── inspections.json
│   │       ├── toolbox-talks.json
│   │       ├── hazards.json
│   │       ├── incidents.json
│   │       ├── workers.json
│   │       └── ... (mirrors en/)
│   └── language-detector.ts      # Browser/user preference detection
│
└── service-worker/               # Offline support
    ├── sw.ts                     # Service worker entry
    ├── cache-strategies.ts       # Network-first, cache-first rules
    ├── sync-manager.ts           # Background sync for queued actions
    └── indexed-db.ts             # Local storage for offline data
```

### Migration from current structure

The existing code maps cleanly:

| Current location | New location |
|---|---|
| `src/App.tsx` | `src/app/App.tsx` |
| `src/main.tsx` | `src/app/main.tsx` |
| `src/lib/api.ts` | `src/lib/api/client.ts` |
| `src/lib/constants.ts` | Split into `src/lib/constants.ts` + `src/types/models.ts` |
| `src/hooks/useAuth.ts` | `src/hooks/useAuth.ts` (unchanged) |
| `src/hooks/useDocuments.ts` | `src/features/documents/useDocuments.ts` |
| `src/hooks/useCompany.ts` | `src/features/company/useCompany.ts` |
| `src/components/*` | `src/components/*` (same structure, expanded) |

---

## 2. ROUTING ARCHITECTURE

### Route definitions

All routes are defined centrally in `src/app/router.tsx` and referenced via the `ROUTES` constant.

```typescript
// src/lib/constants.ts — ROUTES constant (full version)

export const ROUTES = {
  // === Public routes ===
  LANDING: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  BLOG: '/blog',
  BLOG_POST: (slug: string) => `/blog/${slug}`,
  PRICING: '/pricing',
  OSHA_QUIZ: '/osha-readiness',

  // === Authenticated routes (no project scope) ===
  DASHBOARD: '/dashboard',
  ONBOARDING: '/onboarding',

  // --- Projects ---
  PROJECTS: '/projects',
  PROJECT_NEW: '/projects/new',
  PROJECT_DETAIL: (projectId: string) => `/projects/${projectId}`,
  PROJECT_SETTINGS: (projectId: string) => `/projects/${projectId}/settings`,

  // === Project-scoped routes ===
  // Documents
  PROJECT_DOCUMENTS: (projectId: string) => `/projects/${projectId}/documents`,
  PROJECT_DOCUMENT_NEW: (projectId: string) => `/projects/${projectId}/documents/new`,
  PROJECT_DOCUMENT_EDIT: (projectId: string, docId: string) =>
    `/projects/${projectId}/documents/${docId}`,

  // Inspections
  PROJECT_INSPECTIONS: (projectId: string) => `/projects/${projectId}/inspections`,
  PROJECT_INSPECTION_NEW: (projectId: string) => `/projects/${projectId}/inspections/new`,
  PROJECT_INSPECTION_DETAIL: (projectId: string, inspectionId: string) =>
    `/projects/${projectId}/inspections/${inspectionId}`,

  // Toolbox Talks
  PROJECT_TOOLBOX_TALKS: (projectId: string) => `/projects/${projectId}/toolbox-talks`,
  PROJECT_TOOLBOX_TALK_NEW: (projectId: string) => `/projects/${projectId}/toolbox-talks/new`,
  PROJECT_TOOLBOX_TALK_DELIVER: (projectId: string, talkId: string) =>
    `/projects/${projectId}/toolbox-talks/${talkId}/deliver`,
  PROJECT_TOOLBOX_TALK_DETAIL: (projectId: string, talkId: string) =>
    `/projects/${projectId}/toolbox-talks/${talkId}`,

  // Hazards
  PROJECT_HAZARDS: (projectId: string) => `/projects/${projectId}/hazards`,
  PROJECT_HAZARD_NEW: (projectId: string) => `/projects/${projectId}/hazards/new`,
  PROJECT_HAZARD_DETAIL: (projectId: string, hazardId: string) =>
    `/projects/${projectId}/hazards/${hazardId}`,

  // Incidents
  PROJECT_INCIDENTS: (projectId: string) => `/projects/${projectId}/incidents`,
  PROJECT_INCIDENT_NEW: (projectId: string) => `/projects/${projectId}/incidents/new`,
  PROJECT_INCIDENT_DETAIL: (projectId: string, incidentId: string) =>
    `/projects/${projectId}/incidents/${incidentId}`,

  // Morning Brief
  PROJECT_MORNING_BRIEF: (projectId: string) => `/projects/${projectId}/morning-brief`,

  // Equipment (project-scoped)
  PROJECT_EQUIPMENT: (projectId: string) => `/projects/${projectId}/equipment`,
  PROJECT_EQUIPMENT_INSPECT: (projectId: string, equipmentId: string) =>
    `/projects/${projectId}/equipment/${equipmentId}/inspect`,

  // === Non-project-scoped authenticated routes ===
  // Documents (global view across all projects)
  DOCUMENTS: '/documents',
  DOCUMENT_NEW: '/documents/new',
  DOCUMENT_EDIT: (id: string) => `/documents/${id}`,

  // Workers (company-wide)
  WORKERS: '/workers',
  WORKER_NEW: '/workers/new',
  WORKER_DETAIL: (workerId: string) => `/workers/${workerId}`,
  WORKER_CERTIFICATIONS: (workerId: string) => `/workers/${workerId}/certifications`,

  // Equipment (company-wide registry)
  EQUIPMENT: '/equipment',
  EQUIPMENT_NEW: '/equipment/new',
  EQUIPMENT_DETAIL: (equipmentId: string) => `/equipment/${equipmentId}`,

  // Training
  TRAINING: '/training',
  TRAINING_MATRIX: '/training/matrix',

  // Mock OSHA Inspection
  MOCK_INSPECTION: '/mock-inspection',
  MOCK_INSPECTION_NEW: '/mock-inspection/new',
  MOCK_INSPECTION_RESULT: (inspectionId: string) => `/mock-inspection/${inspectionId}`,

  // Analytics
  ANALYTICS: '/analytics',
  ANALYTICS_EMR: '/analytics/emr',
  ANALYTICS_OSHA300: '/analytics/osha-300',

  // Prequalification (Phase 3)
  PREQUALIFICATION: '/prequalification',
  PREQUALIFICATION_SUBMISSION: (submissionId: string) =>
    `/prequalification/${submissionId}`,

  // Settings
  SETTINGS: '/settings',
  SETTINGS_USERS: '/settings/users',
  SETTINGS_NOTIFICATIONS: '/settings/notifications',
  SETTINGS_INTEGRATIONS: '/settings/integrations',

  // Billing
  BILLING: '/billing',

  // Templates (legacy — merges into document create flow)
  TEMPLATES: '/templates',
} as const;
```

### Router structure

```typescript
// src/app/router.tsx

import { lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';

// Lazy-loaded page components (route-based code splitting)
const LandingPage = lazy(() => import('@/components/landing/LandingPage'));
const LoginPage = lazy(() => import('@/components/auth/LoginPage'));
const SignUpPage = lazy(() => import('@/components/auth/SignUpPage'));
const BlogListPage = lazy(() => import('@/components/blog/BlogListPage'));
const BlogPostPage = lazy(() => import('@/components/blog/BlogPostPage'));

const DashboardPage = lazy(() => import('@/components/dashboard/DashboardPage'));
const ProjectListPage = lazy(() => import('@/components/projects/ProjectListPage'));
const ProjectCreatePage = lazy(() => import('@/components/projects/ProjectCreatePage'));
const ProjectDetailPage = lazy(() => import('@/components/projects/ProjectDetailPage'));

const DocumentListPage = lazy(() => import('@/components/documents/DocumentListPage'));
const DocumentCreatePage = lazy(() => import('@/components/documents/DocumentCreatePage'));
const DocumentEditPage = lazy(() => import('@/components/documents/DocumentEditPage'));

const InspectionListPage = lazy(() => import('@/components/inspections/InspectionListPage'));
const InspectionCreatePage = lazy(() => import('@/components/inspections/InspectionCreatePage'));
const InspectionDetailPage = lazy(() => import('@/components/inspections/InspectionDetailPage'));

const ToolboxTalkListPage = lazy(() => import('@/components/toolbox-talks/ToolboxTalkListPage'));
const ToolboxTalkDeliverPage = lazy(() => import('@/components/toolbox-talks/ToolboxTalkDeliverPage'));
const ToolboxTalkDetailPage = lazy(() => import('@/components/toolbox-talks/ToolboxTalkDetailPage'));

const HazardListPage = lazy(() => import('@/components/hazards/HazardListPage'));
const HazardReportPage = lazy(() => import('@/components/hazards/HazardReportPage'));
const HazardDetailPage = lazy(() => import('@/components/hazards/HazardDetailPage'));

const IncidentListPage = lazy(() => import('@/components/incidents/IncidentListPage'));
const IncidentReportPage = lazy(() => import('@/components/incidents/IncidentReportPage'));
const IncidentDetailPage = lazy(() => import('@/components/incidents/IncidentDetailPage'));

const WorkerListPage = lazy(() => import('@/components/workers/WorkerListPage'));
const WorkerDetailPage = lazy(() => import('@/components/workers/WorkerDetailPage'));

const MorningBriefPage = lazy(() => import('@/components/morning-brief/MorningBriefPage'));
const MockInspectionPage = lazy(() => import('@/components/mock-inspection/MockInspectionPage'));
const MockInspectionResults = lazy(() => import('@/components/mock-inspection/MockInspectionResults'));

const AnalyticsDashboard = lazy(() => import('@/components/analytics/AnalyticsDashboard'));
const Osha300Page = lazy(() => import('@/components/analytics/Osha300Page'));
const EmrModelingPage = lazy(() => import('@/components/analytics/EmrModelingPage'));

const TrainingDashboard = lazy(() => import('@/components/training/TrainingDashboard'));
const EquipmentListPage = lazy(() => import('@/components/equipment/EquipmentListPage'));

const CompanySettingsPage = lazy(() => import('@/components/settings/CompanySettingsPage'));
const BillingPage = lazy(() => import('@/components/billing/BillingPage'));

export const router = createBrowserRouter([
  // --- Public ---
  { path: '/', element: <PublicRoute fallback={<Navigate to="/dashboard" />}><LandingPage /></PublicRoute> },
  { path: '/login', element: <PublicRoute fallback={<Navigate to="/dashboard" />}><LoginPage /></PublicRoute> },
  { path: '/signup', element: <PublicRoute fallback={<Navigate to="/dashboard" />}><SignUpPage /></PublicRoute> },
  { path: '/blog', element: <BlogListPage /> },
  { path: '/blog/:slug', element: <BlogPostPage /> },
  { path: '/pricing', element: <LandingPage /> }, // anchor scroll to pricing
  { path: '/osha-readiness', element: <LandingPage /> }, // quiz component

  // --- Authenticated shell ---
  {
    element: <ProtectedRoute><AppLayout /></ProtectedRoute>,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/onboarding', element: <OnboardingWizard /> },

      // Projects
      { path: '/projects', element: <ProjectListPage /> },
      { path: '/projects/new', element: <ProjectCreatePage /> },
      { path: '/projects/:projectId', element: <ProjectDetailPage /> },
      { path: '/projects/:projectId/settings', element: <ProjectSettingsPage /> },

      // Project-scoped features
      { path: '/projects/:projectId/documents', element: <DocumentListPage /> },
      { path: '/projects/:projectId/documents/new', element: <DocumentCreatePage /> },
      { path: '/projects/:projectId/documents/:docId', element: <DocumentEditPage /> },

      { path: '/projects/:projectId/inspections', element: <InspectionListPage /> },
      { path: '/projects/:projectId/inspections/new', element: <InspectionCreatePage /> },
      { path: '/projects/:projectId/inspections/:inspectionId', element: <InspectionDetailPage /> },

      { path: '/projects/:projectId/toolbox-talks', element: <ToolboxTalkListPage /> },
      { path: '/projects/:projectId/toolbox-talks/new', element: <ToolboxTalkDeliverPage /> },
      { path: '/projects/:projectId/toolbox-talks/:talkId', element: <ToolboxTalkDetailPage /> },
      { path: '/projects/:projectId/toolbox-talks/:talkId/deliver', element: <ToolboxTalkDeliverPage /> },

      { path: '/projects/:projectId/hazards', element: <HazardListPage /> },
      { path: '/projects/:projectId/hazards/new', element: <HazardReportPage /> },
      { path: '/projects/:projectId/hazards/:hazardId', element: <HazardDetailPage /> },

      { path: '/projects/:projectId/incidents', element: <IncidentListPage /> },
      { path: '/projects/:projectId/incidents/new', element: <IncidentReportPage /> },
      { path: '/projects/:projectId/incidents/:incidentId', element: <IncidentDetailPage /> },

      { path: '/projects/:projectId/morning-brief', element: <MorningBriefPage /> },

      { path: '/projects/:projectId/equipment', element: <EquipmentListPage /> },
      { path: '/projects/:projectId/equipment/:equipmentId/inspect', element: <EquipmentInspectionPage /> },

      // Global document views (legacy + cross-project)
      { path: '/documents', element: <DocumentListPage /> },
      { path: '/documents/new', element: <DocumentCreatePage /> },
      { path: '/documents/:id', element: <DocumentEditPage /> },

      // Company-wide features
      { path: '/workers', element: <WorkerListPage /> },
      { path: '/workers/new', element: <WorkerCreatePage /> },
      { path: '/workers/:workerId', element: <WorkerDetailPage /> },
      { path: '/workers/:workerId/certifications', element: <CertificationTracker /> },

      { path: '/equipment', element: <EquipmentListPage /> },
      { path: '/equipment/new', element: <EquipmentCreatePage /> },
      { path: '/equipment/:equipmentId', element: <EquipmentDetailPage /> },

      { path: '/training', element: <TrainingDashboard /> },
      { path: '/training/matrix', element: <TrainingMatrix /> },

      { path: '/mock-inspection', element: <MockInspectionHistory /> },
      { path: '/mock-inspection/new', element: <MockInspectionPage /> },
      { path: '/mock-inspection/:inspectionId', element: <MockInspectionResults /> },

      { path: '/analytics', element: <AnalyticsDashboard /> },
      { path: '/analytics/emr', element: <EmrModelingPage /> },
      { path: '/analytics/osha-300', element: <Osha300Page /> },

      { path: '/prequalification', element: <PrequalDashboard /> },
      { path: '/prequalification/:submissionId', element: <PrequalSubmissionPage /> },

      { path: '/settings', element: <CompanySettingsPage /> },
      { path: '/settings/users', element: <UserManagementPage /> },
      { path: '/settings/notifications', element: <NotificationSettings /> },
      { path: '/settings/integrations', element: <IntegrationSettings /> },

      { path: '/billing', element: <BillingPage /> },

      // Legacy redirect
      { path: '/templates', element: <Navigate to="/documents/new" replace /> },
    ],
  },
]);
```

### Navigation structure

**Desktop sidebar** groups routes into sections:

| Section | Items |
|---|---|
| Overview | Dashboard |
| Field Operations | Morning Brief, Inspections, Toolbox Talks, Hazard Reports |
| Documentation | Documents, Templates |
| Investigations | Incidents |
| People | Workers, Training |
| Equipment | Equipment Registry |
| Compliance | Mock Inspection, Analytics, OSHA 300 Log |
| Prequalification | ISN/Avetta (Phase 3) |
| Settings | Company, Users, Billing |

**Mobile bottom tab bar** shows 5 items contextual to the current project:

| Tab | Icon | Route |
|---|---|---|
| Brief | Sun | `/projects/:id/morning-brief` |
| Inspect | ClipboardCheck | `/projects/:id/inspections/new` |
| Talk | MessageSquare | `/projects/:id/toolbox-talks` |
| Hazard | AlertTriangle | `/projects/:id/hazards/new` |
| More | Menu | Opens the full sidebar |

---

## 3. STATE MANAGEMENT

### Decision matrix

| State type | Technology | Examples |
|---|---|---|
| Server state (CRUD resources) | TanStack React Query | Documents, inspections, projects, workers |
| Auth state | React Context (`AuthContext`) | Current user, token, demo mode |
| Current project | React Context (`ProjectContext`) | Selected project ID, project data |
| Language preference | React Context (`I18nContext`) | Current locale, direction |
| Connectivity status | React Context (`OfflineContext`) | Online/offline, pending sync count |
| Form state | React local state (`useState`) | Input values within a form |
| UI ephemeral state | React local state | Dialogs, dropdowns, editing modes |
| Offline queue | IndexedDB + custom hook | Mutations queued while offline |

There is no Redux, Zustand, or Jotai. The app does not have state complex enough to justify a dedicated state library. React Query handles the majority of complexity (server cache, loading states, optimistic updates, refetching).

### React Query conventions

**Query key factory pattern:**

```typescript
// src/lib/query-keys.ts

export const queryKeys = {
  // Projects
  projects: {
    all: ['projects'] as const,
    list: (filters?: ProjectFilters) => ['projects', 'list', filters] as const,
    detail: (id: string) => ['projects', 'detail', id] as const,
  },

  // Documents (project-scoped)
  documents: {
    all: (projectId?: string) => ['documents', { projectId }] as const,
    list: (projectId: string, filters?: DocumentFilters) =>
      ['documents', 'list', projectId, filters] as const,
    detail: (id: string) => ['documents', 'detail', id] as const,
    stats: (projectId?: string) => ['documents', 'stats', { projectId }] as const,
  },

  // Inspections
  inspections: {
    all: (projectId: string) => ['inspections', { projectId }] as const,
    list: (projectId: string, filters?: InspectionFilters) =>
      ['inspections', 'list', projectId, filters] as const,
    detail: (id: string) => ['inspections', 'detail', id] as const,
  },

  // Toolbox Talks
  toolboxTalks: {
    all: (projectId: string) => ['toolbox-talks', { projectId }] as const,
    list: (projectId: string, filters?: ToolboxTalkFilters) =>
      ['toolbox-talks', 'list', projectId, filters] as const,
    detail: (id: string) => ['toolbox-talks', 'detail', id] as const,
  },

  // Hazards
  hazards: {
    all: (projectId: string) => ['hazards', { projectId }] as const,
    list: (projectId: string, filters?: HazardFilters) =>
      ['hazards', 'list', projectId, filters] as const,
    detail: (id: string) => ['hazards', 'detail', id] as const,
  },

  // Incidents
  incidents: {
    all: (projectId?: string) => ['incidents', { projectId }] as const,
    list: (projectId: string, filters?: IncidentFilters) =>
      ['incidents', 'list', projectId, filters] as const,
    detail: (id: string) => ['incidents', 'detail', id] as const,
  },

  // Workers
  workers: {
    all: [] as const,
    list: (filters?: WorkerFilters) => ['workers', 'list', filters] as const,
    detail: (id: string) => ['workers', 'detail', id] as const,
    certifications: (workerId: string) =>
      ['workers', workerId, 'certifications'] as const,
  },

  // Equipment
  equipment: {
    all: [] as const,
    list: (filters?: EquipmentFilters) => ['equipment', 'list', filters] as const,
    detail: (id: string) => ['equipment', 'detail', id] as const,
    inspections: (equipmentId: string) =>
      ['equipment', equipmentId, 'inspections'] as const,
  },

  // Morning Brief
  morningBrief: {
    today: (projectId: string) => ['morning-brief', projectId, 'today'] as const,
    history: (projectId: string) => ['morning-brief', projectId, 'history'] as const,
  },

  // Mock Inspection
  mockInspection: {
    all: [] as const,
    detail: (id: string) => ['mock-inspection', 'detail', id] as const,
  },

  // Analytics
  analytics: {
    dashboard: (companyId: string) => ['analytics', companyId] as const,
    emr: (companyId: string) => ['analytics', 'emr', companyId] as const,
    osha300: (companyId: string, year: number) =>
      ['analytics', 'osha300', companyId, year] as const,
  },

  // Company
  company: {
    current: ['company'] as const,
    subscription: ['company', 'subscription'] as const,
  },
} as const;
```

**Cache invalidation strategy:**

| Mutation | Invalidates |
|---|---|
| Create inspection | `inspections.all(projectId)`, `analytics.dashboard` |
| Submit toolbox talk | `toolboxTalks.all(projectId)`, project compliance score |
| Report hazard | `hazards.all(projectId)`, `analytics.dashboard` |
| Update worker certification | `workers.certifications(workerId)`, `workers.detail(workerId)` |
| Run mock inspection | `mockInspection.all`, `analytics.dashboard` |
| Create/update project | `projects.all`, `projects.detail(id)` |

**Optimistic updates for field-critical actions:**

Inspections, toolbox talk sign-offs, and hazard reports use optimistic updates so the UI responds instantly even on slow connections. The mutation writes to IndexedDB immediately and enqueues the API call. If the API call fails while offline, it stays in the queue.

```typescript
// Pattern for optimistic mutation with offline support
export function useCreateInspection(projectId: string) {
  const queryClient = useQueryClient();
  const { enqueueOfflineMutation } = useOffline();

  return useMutation({
    mutationFn: async (data: CreateInspectionPayload) => {
      return api.post<Inspection>(
        `/projects/${projectId}/inspections`,
        data
      );
    },
    onMutate: async (newInspection) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.inspections.all(projectId),
      });

      const optimistic: Inspection = {
        id: `temp_${Date.now()}`,
        ...newInspection,
        status: 'submitted',
        created_at: new Date().toISOString(),
        synced: false,
      };

      queryClient.setQueryData(
        queryKeys.inspections.list(projectId),
        (old: Inspection[] = []) => [optimistic, ...old]
      );

      // Persist to IndexedDB for offline
      await saveToIndexedDB('inspections', optimistic);

      return { optimistic };
    },
    onError: (_err, _vars, context) => {
      // Revert optimistic update on error
      queryClient.invalidateQueries({
        queryKey: queryKeys.inspections.all(projectId),
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.inspections.all(projectId),
      });
    },
  });
}
```

### Global context shapes

```typescript
// ProjectContext
interface ProjectContextType {
  currentProjectId: string | null;
  currentProject: Project | null;
  setCurrentProject: (projectId: string) => void;
  isLoading: boolean;
}

// OfflineContext
interface OfflineContextType {
  isOnline: boolean;
  pendingSyncCount: number;
  lastSyncAt: Date | null;
  syncNow: () => Promise<void>;
  enqueueOfflineMutation: (mutation: QueuedMutation) => Promise<void>;
}
```

---

## 4. DATA TYPES (TypeScript)

All domain models live in `src/types/models.ts`. These match the backend Pydantic models.

```typescript
// ============================================================
// COMMON TYPES
// ============================================================

/** ISO 8601 date-time string */
type ISODateTime = string;

/** ISO 8601 date string (YYYY-MM-DD) */
type ISODate = string;

/** Firestore document ID (e.g., "proj_a1b2c3d4e5f6g7h8") */
type EntityId = string;

/** GPS coordinates */
interface GeoPoint {
  latitude: number;
  longitude: number;
  accuracy_meters?: number;
}

/** Audit fields present on all entities */
interface AuditFields {
  created_at: ISODateTime;
  created_by: string;
  updated_at: ISODateTime;
  updated_by: string;
}

/** Supported languages */
type Language = 'en' | 'es';

/** Risk level used across features */
type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

/** Compliance status for dashboard indicators */
type ComplianceStatus = 'compliant' | 'at_risk' | 'non_compliant';

/** Media attachment (photo, voice, file) */
interface Attachment {
  id: EntityId;
  type: 'photo' | 'voice' | 'document';
  url: string;
  thumbnail_url?: string;
  filename: string;
  size_bytes: number;
  mime_type: string;
  geo_point?: GeoPoint;
  captured_at: ISODateTime;
}

// ============================================================
// USER & AUTH
// ============================================================

type UserRole = 'owner' | 'admin' | 'foreman' | 'worker' | 'viewer';

interface User {
  id: EntityId;
  company_id: EntityId;
  email: string;
  display_name: string;
  role: UserRole;
  language_preference: Language;
  phone?: string;
  photo_url?: string;
  is_active: boolean;
  last_login_at?: ISODateTime;
}

interface AuthState {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  isDemoMode: boolean;
  isAuthenticated: boolean;
}

// ============================================================
// COMPANY & SUBSCRIPTION
// ============================================================

type SubscriptionTier = 'starter' | 'professional' | 'business' | 'enterprise';
type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'trialing';

interface Company extends AuditFields {
  id: EntityId;
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  phone: string;
  email: string;
  license_number?: string;
  ein?: string;
  safety_officer_name?: string;
  safety_officer_phone?: string;
  safety_officer_email?: string;
  logo_url?: string;
  trades: Trade[];
  employee_count: number;
  subscription: Subscription;
}

interface Subscription {
  tier: SubscriptionTier;
  status: SubscriptionStatus;
  active_project_limit: number;
  active_project_count: number;
  renewal_date: ISODate;
  trial_ends_at?: ISODateTime;
  stripe_customer_id?: string;
}

type Trade =
  | 'general'
  | 'electrical'
  | 'plumbing'
  | 'hvac'
  | 'concrete'
  | 'roofing'
  | 'framing'
  | 'carpentry'
  | 'welding'
  | 'demolition'
  | 'excavation'
  | 'painting'
  | 'steelwork'
  | 'masonry'
  | 'insulation'
  | 'flooring'
  | 'drywall'
  | 'landscaping';

// ============================================================
// PROJECT
// ============================================================

type ProjectStatus = 'planning' | 'active' | 'paused' | 'completed' | 'archived';
type ProjectType = 'commercial' | 'residential' | 'industrial' | 'infrastructure' | 'renovation';

interface Project extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  geo_point?: GeoPoint;
  project_type: ProjectType;
  status: ProjectStatus;
  client_name: string;
  start_date: ISODate;
  estimated_end_date: ISODate;
  actual_end_date?: ISODate;
  trades_on_site: Trade[];
  peak_worker_count: number;
  description?: string;
  gc_name?: string;
  gc_contact_email?: string;
  compliance_score: number;         // 0-100
  compliance_status: ComplianceStatus;
  special_hazards?: string[];
}

interface ProjectSummary {
  id: EntityId;
  name: string;
  status: ProjectStatus;
  compliance_score: number;
  compliance_status: ComplianceStatus;
  open_hazards: number;
  overdue_inspections: number;
  last_inspection_at?: ISODateTime;
  last_toolbox_talk_at?: ISODateTime;
}

// ============================================================
// DOCUMENT
// ============================================================

type DocumentType =
  | 'safety_plan'
  | 'jha'
  | 'toolbox_talk'
  | 'incident_report'
  | 'emergency_plan'
  | 'hazcom_program'
  | 'fall_protection_plan'
  | 'excavation_plan'
  | 'scaffolding_plan'
  | 'lockout_tagout'
  | 'ppe_program'
  | 'electrical_safety'
  | 'confined_space'
  | 'crane_lift_plan'
  | 'hot_work_permit'
  | 'respiratory_protection';

type DocumentStatus = 'draft' | 'final' | 'archived' | 'superseded';

interface Document extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  project_id?: EntityId;
  title: string;
  document_type: DocumentType;
  status: DocumentStatus;
  language: Language;
  content: DocumentContent;
  field_data: Record<string, string>;
  version: number;
  osha_references: string[];        // e.g., ["1926.502(d)", "1926.651(j)(2)"]
  ai_confidence_score?: number;     // 0-1
  reviewed_by?: string;
  reviewed_at?: ISODateTime;
}

interface DocumentContent {
  sections: DocumentSection[];
}

interface DocumentSection {
  id: string;
  title: string;
  content: string;
  language: Language;
  osha_references?: string[];
}

// ============================================================
// INSPECTION
// ============================================================

type InspectionStatus = 'in_progress' | 'submitted' | 'reviewed';
type InspectionType = 'daily' | 'weekly' | 'pre_task' | 'equipment' | 'safety_walk';

interface Inspection extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  project_id: EntityId;
  type: InspectionType;
  status: InspectionStatus;
  inspector_id: EntityId;
  inspector_name: string;
  date: ISODate;
  geo_point?: GeoPoint;
  weather_conditions?: string;
  temperature_f?: number;
  checklist_items: InspectionChecklistItem[];
  notes?: string;
  attachments: Attachment[];
  findings_count: number;
  corrective_actions_count: number;
  synced: boolean;                  // false if created offline
}

interface InspectionChecklistItem {
  id: string;
  category: string;
  description: string;
  status: 'pass' | 'fail' | 'na' | 'not_inspected';
  notes?: string;
  photo_ids?: string[];
  osha_reference?: string;
}

// ============================================================
// TOOLBOX TALK
// ============================================================

type ToolboxTalkStatus = 'draft' | 'ready' | 'delivered' | 'archived';

interface ToolboxTalk extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  project_id: EntityId;
  title: string;
  topic: string;
  content_en: string;
  content_es: string;
  status: ToolboxTalkStatus;
  duration_minutes: number;
  trade_focus?: Trade;
  osha_references: string[];
  delivered_at?: ISODateTime;
  delivered_by?: EntityId;
  attendees: ToolboxTalkAttendee[];
  geo_point?: GeoPoint;
  ai_generated: boolean;
}

interface ToolboxTalkAttendee {
  worker_id: EntityId;
  worker_name: string;
  signature_url?: string;
  signed_at?: ISODateTime;
  language_viewed: Language;
}

// ============================================================
// HAZARD REPORT
// ============================================================

type HazardSeverity = 'low' | 'medium' | 'high' | 'imminent_danger';
type HazardStatus = 'reported' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed';

interface HazardReport extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  project_id: EntityId;
  reporter_id: EntityId;
  reporter_name: string;
  is_anonymous: boolean;
  description: string;
  voice_note_url?: string;
  voice_transcription?: string;
  location_description: string;
  geo_point?: GeoPoint;
  severity: HazardSeverity;
  status: HazardStatus;
  photos: Attachment[];
  ai_analysis?: HazardAiAnalysis;
  osha_references: string[];
  corrective_action?: string;
  resolved_at?: ISODateTime;
  resolved_by?: EntityId;
}

interface HazardAiAnalysis {
  identified_hazards: string[];
  risk_level: RiskLevel;
  applicable_standards: OshaStandard[];
  recommended_actions: string[];
  confidence_score: number;        // 0-1
}

interface OshaStandard {
  code: string;                    // e.g., "1926.652(a)(1)"
  title: string;
  summary: string;
}

// ============================================================
// INCIDENT
// ============================================================

type IncidentType = 'injury' | 'near_miss' | 'property_damage' | 'environmental' | 'equipment_failure';
type IncidentSeverity = 'first_aid' | 'medical_treatment' | 'lost_time' | 'fatality';
type IncidentStatus = 'reported' | 'investigating' | 'corrective_action' | 'closed';

interface Incident extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  project_id: EntityId;
  incident_type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  incident_date: ISODate;
  incident_time: string;           // "HH:MM" format
  location_description: string;
  geo_point?: GeoPoint;
  description: string;
  voice_note_url?: string;
  voice_transcription?: string;
  persons_involved: IncidentPerson[];
  witnesses: IncidentWitness[];
  immediate_actions_taken: string;
  root_causes?: string[];
  corrective_actions: CorrectiveAction[];
  attachments: Attachment[];
  osha_recordable: boolean;
  osha_301_generated: boolean;
  timeline_events: TimelineEvent[];
}

interface IncidentPerson {
  name: string;
  role: string;
  injury_description?: string;
  treatment_provided?: string;
  days_away?: number;
  days_restricted?: number;
}

interface IncidentWitness {
  name: string;
  phone?: string;
  statement?: string;
}

interface CorrectiveAction {
  id: string;
  description: string;
  assigned_to: string;
  due_date: ISODate;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  completed_at?: ISODateTime;
}

interface TimelineEvent {
  id: string;
  timestamp: ISODateTime;
  event_type: 'incident' | 'first_aid' | 'notification' | 'investigation' | 'action' | 'closure';
  description: string;
  actor?: string;
}

// ============================================================
// WORKER & CERTIFICATION
// ============================================================

interface Worker extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  first_name: string;
  last_name: string;
  full_name: string;               // computed
  email?: string;
  phone?: string;
  language_preference: Language;
  trade: Trade;
  hire_date: ISODate;
  is_active: boolean;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  certifications: Certification[];
  photo_url?: string;
  projects: EntityId[];            // project IDs currently assigned to
}

type CertificationType =
  | 'osha_10'
  | 'osha_30'
  | 'fall_protection'
  | 'scaffold_competent_person'
  | 'confined_space'
  | 'excavation_competent_person'
  | 'first_aid_cpr'
  | 'forklift'
  | 'crane_operator'
  | 'rigging_signaling'
  | 'hazmat'
  | 'silica_competent_person'
  | 'lead_competent_person'
  | 'aerial_lift'
  | 'welding_hot_work'
  | 'electrical_qualified'
  | 'traffic_control'
  | 'trench_safety';

type CertificationStatus = 'valid' | 'expiring_soon' | 'expired' | 'not_held';

interface Certification {
  id: EntityId;
  worker_id: EntityId;
  type: CertificationType;
  issue_date: ISODate;
  expiration_date?: ISODate;
  issuing_organization: string;
  certificate_number?: string;
  document_url?: string;           // uploaded proof
  status: CertificationStatus;     // computed from expiration_date
}

interface TrainingRecord extends AuditFields {
  id: EntityId;
  worker_id: EntityId;
  company_id: EntityId;
  training_type: string;
  title: string;
  completed_date: ISODate;
  expiration_date?: ISODate;
  provider: string;
  hours: number;
  document_url?: string;
  language: Language;
}

// ============================================================
// EQUIPMENT
// ============================================================

type EquipmentType =
  | 'crane'
  | 'forklift'
  | 'aerial_lift'
  | 'scaffold'
  | 'excavator'
  | 'loader'
  | 'compressor'
  | 'generator'
  | 'welding_machine'
  | 'saw'
  | 'ladder'
  | 'harness'
  | 'vehicle'
  | 'other';

type EquipmentStatus = 'operational' | 'needs_repair' | 'out_of_service' | 'retired';

interface Equipment extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  name: string;
  type: EquipmentType;
  make?: string;
  model?: string;
  serial_number?: string;
  year?: number;
  status: EquipmentStatus;
  assigned_project_id?: EntityId;
  last_inspection_date?: ISODate;
  next_inspection_due?: ISODate;
  certification_required: boolean;
  certification_expiry?: ISODate;
  photo_url?: string;
}

interface EquipmentInspection extends AuditFields {
  id: EntityId;
  equipment_id: EntityId;
  project_id: EntityId;
  inspector_id: EntityId;
  inspector_name: string;
  date: ISODate;
  checklist_items: InspectionChecklistItem[];
  result: 'pass' | 'fail' | 'conditional';
  notes?: string;
  attachments: Attachment[];
  next_inspection_due: ISODate;
}

// ============================================================
// MOCK OSHA INSPECTION
// ============================================================

type FindingSeverity = 'other_than_serious' | 'serious' | 'willful' | 'repeat';
type FindingStatus = 'open' | 'in_progress' | 'remediated' | 'accepted';

interface MockInspectionResult extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  readiness_score: number;         // 0-100
  previous_score?: number;
  score_change: number;
  findings: MockInspectionFinding[];
  findings_by_severity: Record<FindingSeverity, number>;
  areas_reviewed: string[];
  recommendations: string[];
  next_review_date: ISODate;
}

interface MockInspectionFinding {
  id: string;
  osha_standard: string;           // e.g., "29 CFR 1926.502(d)(1)"
  standard_title: string;
  severity: FindingSeverity;
  status: FindingStatus;
  observed_condition: string;
  required_condition: string;
  recommended_corrective_action: string;
  affected_projects: EntityId[];
  estimated_penalty_range?: {
    min: number;
    max: number;
  };
}

// ============================================================
// MORNING BRIEF
// ============================================================

interface MorningBrief {
  id: EntityId;
  project_id: EntityId;
  date: ISODate;
  risk_score: number;              // 0-10
  risk_level: RiskLevel;
  weather: WeatherData;
  alerts: BriefAlert[];
  recommended_toolbox_talk?: {
    id: EntityId;
    title: string;
    reason: string;
  };
  certification_warnings: CertificationWarning[];
  open_hazards: number;
  overdue_inspections: number;
  generated_at: ISODateTime;
}

interface WeatherData {
  temperature_f: number;
  conditions: string;
  wind_speed_mph: number;
  humidity_percent: number;
  heat_index_f?: number;
  wind_chill_f?: number;
  precipitation_chance: number;
  alerts: string[];
}

interface BriefAlert {
  id: string;
  type: 'weather' | 'certification' | 'inspection' | 'hazard' | 'incident' | 'regulation';
  severity: RiskLevel;
  title: string;
  description: string;
  action_required: string;
  osha_reference?: string;
}

interface CertificationWarning {
  worker_id: EntityId;
  worker_name: string;
  certification_type: CertificationType;
  expiration_date: ISODate;
  days_until_expiry: number;
  restriction?: string;            // e.g., "May not enter excavation"
}

// ============================================================
// ANALYTICS & OSHA 300
// ============================================================

interface CompanyAnalytics {
  compliance_score: number;
  compliance_trend: TrendPoint[];
  incident_rate: number;
  dart_rate: number;
  emr: number;
  emr_projected: number;
  total_inspections_30d: number;
  total_toolbox_talks_30d: number;
  total_hazard_reports_30d: number;
  open_corrective_actions: number;
  projects_by_status: Record<ComplianceStatus, number>;
}

interface TrendPoint {
  date: ISODate;
  value: number;
}

interface Osha300Log {
  year: number;
  company_id: EntityId;
  entries: Osha300Entry[];
  summary: Osha300Summary;
}

interface Osha300Entry {
  case_number: string;
  employee_name: string;
  job_title: string;
  date_of_injury: ISODate;
  where_event_occurred: string;
  description: string;
  classify: 'death' | 'days_away' | 'restricted' | 'other_recordable';
  days_away: number;
  days_restricted: number;
  injury_type: string;
}

interface Osha300Summary {
  total_cases: number;
  total_deaths: number;
  total_days_away_cases: number;
  total_restricted_cases: number;
  total_other_recordable: number;
  total_days_away: number;
  total_days_restricted: number;
  incidence_rate: number;
  dart_rate: number;
}

// ============================================================
// PREQUALIFICATION (Phase 3)
// ============================================================

type PrequalPlatform = 'isnetworld' | 'avetta' | 'browz';
type PrequalStatus = 'not_started' | 'in_progress' | 'submitted' | 'approved' | 'expired';

interface PrequalSubmission extends AuditFields {
  id: EntityId;
  company_id: EntityId;
  platform: PrequalPlatform;
  status: PrequalStatus;
  due_date: ISODate;
  auto_filled_percent: number;
  missing_documents: string[];
  submitted_at?: ISODateTime;
  approved_at?: ISODateTime;
}

// ============================================================
// API ENVELOPES
// ============================================================

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}
```

---

## 5. API CLIENT ARCHITECTURE

### Base client (refactored from current `api.ts`)

The current `api.ts` is a solid foundation. It is refactored into a module structure with interceptors and resource-specific methods.

```typescript
// src/lib/api/client.ts

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export class ApiClient {
  private baseUrl: string;
  private interceptors: RequestInterceptor[] = [];

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  addInterceptor(interceptor: RequestInterceptor): void {
    this.interceptors.push(interceptor);
  }

  async request<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    let config: ApiRequestConfig = {
      url: `${this.baseUrl}${endpoint}`,
      method: options.method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: options.body,
    };

    // Run request interceptors
    for (const interceptor of this.interceptors) {
      if (interceptor.onRequest) {
        config = await interceptor.onRequest(config);
      }
    }

    try {
      const response = await fetch(config.url, {
        method: config.method,
        headers: config.headers,
        body: config.body ? JSON.stringify(config.body) : undefined,
        signal: options.signal,
      });

      if (!response.ok) {
        const error = new ApiError(
          response.status,
          response.statusText,
          await response.json().catch(() => null)
        );

        // Run error interceptors
        for (const interceptor of this.interceptors) {
          if (interceptor.onError) {
            await interceptor.onError(error);
          }
        }

        throw error;
      }

      if (response.status === 204) return undefined as T;
      return response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;

      // Network error — could be offline
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('No network connection');
      }

      throw error;
    }
  }

  get<T>(endpoint: string, options?: ApiRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, body?: unknown, options?: ApiRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'POST', body });
  }

  put<T>(endpoint: string, body?: unknown, options?: ApiRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body });
  }

  patch<T>(endpoint: string, body?: unknown, options?: ApiRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'PATCH', body });
  }

  delete<T>(endpoint: string, options?: ApiRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Singleton with interceptors applied
export const api = new ApiClient();
```

### Interceptors

```typescript
// src/lib/api/interceptors.ts

interface RequestInterceptor {
  onRequest?: (config: ApiRequestConfig) => Promise<ApiRequestConfig>;
  onError?: (error: ApiError) => Promise<void>;
}

// Auth interceptor — attaches Firebase ID token
export const authInterceptor: RequestInterceptor = {
  onRequest: async (config) => {
    const token = await getAuthToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  onError: async (error) => {
    if (error.status === 401) {
      window.location.href = '/login';
    }
  },
};

// Error toast interceptor — shows user-facing errors
export const errorToastInterceptor: RequestInterceptor = {
  onError: async (error) => {
    if (error.status === 403) {
      toast.error('Upgrade required', {
        description: 'This feature requires a higher subscription tier.',
        action: { label: 'Upgrade', onClick: () => navigate('/billing') },
      });
    } else if (error.status === 429) {
      toast.error('Rate limited', {
        description: 'Too many requests. Please wait a moment.',
      });
    } else if (error.status >= 500) {
      toast.error('Server error', {
        description: 'Something went wrong. Please try again.',
      });
    }
  },
};

// Offline interceptor — queues mutation if offline
export const offlineInterceptor: RequestInterceptor = {
  onRequest: async (config) => {
    if (!navigator.onLine && config.method !== 'GET') {
      await enqueueOfflineMutation(config);
      throw new OfflineQueuedError('Mutation queued for sync');
    }
    return config;
  },
};
```

### Resource API modules

Each resource gets a thin module that wraps the base client with typed endpoints.

```typescript
// src/lib/api/resources/inspections.api.ts

import { api } from '../client';
import type { Inspection, PaginatedResponse } from '@/types/models';

export interface CreateInspectionPayload {
  project_id: string;
  type: InspectionType;
  date: string;
  checklist_items: InspectionChecklistItem[];
  notes?: string;
  geo_point?: GeoPoint;
}

export const inspectionsApi = {
  list: (projectId: string, params?: Record<string, string>) =>
    api.get<PaginatedResponse<Inspection>>(
      `/projects/${projectId}/inspections`,
      { params }
    ),

  get: (projectId: string, inspectionId: string) =>
    api.get<Inspection>(
      `/projects/${projectId}/inspections/${inspectionId}`
    ),

  create: (projectId: string, data: CreateInspectionPayload) =>
    api.post<Inspection>(
      `/projects/${projectId}/inspections`,
      data
    ),

  update: (projectId: string, inspectionId: string, data: Partial<Inspection>) =>
    api.patch<Inspection>(
      `/projects/${projectId}/inspections/${inspectionId}`,
      data
    ),

  delete: (projectId: string, inspectionId: string) =>
    api.delete(`/projects/${projectId}/inspections/${inspectionId}`),
};
```

This pattern repeats for all 15+ resources: `projects.api.ts`, `documents.api.ts`, `toolbox-talks.api.ts`, `hazards.api.ts`, `incidents.api.ts`, `workers.api.ts`, `equipment.api.ts`, `training.api.ts`, `mock-inspection.api.ts`, `morning-brief.api.ts`, `analytics.api.ts`, `prequalification.api.ts`, `company.api.ts`, `billing.api.ts`.

### File upload

```typescript
// src/lib/api/file-upload.ts

export async function uploadFile(
  file: File | Blob,
  options: {
    type: 'photo' | 'voice' | 'document';
    entity_type: string;    // 'inspection', 'hazard', etc.
    entity_id: string;
    geo_point?: GeoPoint;
  }
): Promise<Attachment> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', options.type);
  formData.append('entity_type', options.entity_type);
  formData.append('entity_id', options.entity_id);
  if (options.geo_point) {
    formData.append('geo_point', JSON.stringify(options.geo_point));
  }

  const token = await getAuthToken();
  const response = await fetch(`${BASE_URL}/uploads`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) throw new ApiError(response.status, 'Upload failed');
  return response.json();
}

// Compress photo before upload (field photos are often 5-12 MB)
export async function compressAndUploadPhoto(
  file: File,
  options: Omit<Parameters<typeof uploadFile>[1], 'type'>
): Promise<Attachment> {
  const compressed = await compressImage(file, {
    maxWidth: 1920,
    maxHeight: 1920,
    quality: 0.8,
    mimeType: 'image/jpeg',
  });
  return uploadFile(compressed, { ...options, type: 'photo' });
}
```

### Offline queue

```typescript
// src/lib/api/offline-queue.ts

interface QueuedMutation {
  id: string;
  timestamp: number;
  url: string;
  method: string;
  body?: unknown;
  retries: number;
}

// Stores in IndexedDB, processes on reconnect
export class OfflineQueue {
  private dbName = 'safetyforge_offline';
  private storeName = 'mutations';

  async enqueue(mutation: Omit<QueuedMutation, 'id' | 'timestamp' | 'retries'>): Promise<void> {
    const entry: QueuedMutation = {
      ...mutation,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retries: 0,
    };
    await this.save(entry);
  }

  async processQueue(): Promise<void> {
    const mutations = await this.getAll();
    for (const mutation of mutations) {
      try {
        await fetch(mutation.url, {
          method: mutation.method,
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${await getAuthToken()}`,
          },
          body: mutation.body ? JSON.stringify(mutation.body) : undefined,
        });
        await this.remove(mutation.id);
      } catch {
        mutation.retries++;
        if (mutation.retries >= 5) {
          await this.remove(mutation.id);
          // Notify user of permanently failed sync
        } else {
          await this.save(mutation);
        }
      }
    }
  }

  // IndexedDB operations (save, getAll, remove) implemented here
}
```

---

## 6. MOBILE-FIRST / FIELD-FIRST DESIGN

This is the most critical architectural decision in SafetyForge. The primary user (Marco the foreman) works outdoors in sun, rain, dust, and noise with gloves on.

### Responsive breakpoints

```typescript
// Tailwind v4 breakpoints (in src/index.css or tailwind config)
// mobile-first: base styles are mobile

// sm: 640px   — large phones in landscape
// md: 768px   — tablets
// lg: 1024px  — small laptops / tablets in landscape
// xl: 1280px  — desktops
// 2xl: 1536px — large desktops

// Custom breakpoint for field vs. office detection:
// field: < 768px (phone in portrait = field worker)
// office: >= 768px (tablet landscape or desktop = office user)
```

### Touch targets

All interactive elements on mobile MUST be at minimum 48x48 CSS pixels (larger than WCAG's 44px, accounting for gloves). This applies to:

- Buttons: `min-h-12 min-w-12` (48px)
- List items: `min-h-14 py-3` (56px row height)
- Checkbox/radio: `h-6 w-6` (24px) within a 48px tap area
- Navigation tabs: `min-h-14`
- Form inputs: `min-h-12 text-base` (avoid zoom on iOS with 16px+ font)

```typescript
// src/components/shared/FieldButton.tsx
// Large touch target button for field use

interface FieldButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  icon?: React.ReactNode;
  disabled?: boolean;
  fullWidth?: boolean;
}

export function FieldButton({
  children,
  onClick,
  variant = 'primary',
  icon,
  disabled,
  fullWidth,
}: FieldButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'flex min-h-14 items-center justify-center gap-3 rounded-xl px-6 text-lg font-semibold',
        'active:scale-[0.97] transition-transform',       // tactile feedback
        fullWidth && 'w-full',
        variant === 'primary' && 'bg-orange-500 text-white active:bg-orange-600',
        variant === 'secondary' && 'bg-slate-100 text-slate-700 active:bg-slate-200',
        variant === 'danger' && 'bg-red-500 text-white active:bg-red-600',
        disabled && 'opacity-50 pointer-events-none',
      )}
    >
      {icon}
      {children}
    </button>
  );
}
```

### Offline support architecture

```
┌─────────────────────────────────────┐
│           React App                  │
│                                     │
│  React Query ←→ API Client         │
│       ↕                ↕            │
│  Query Cache    Offline Queue       │
│       ↕                ↕            │
│  ┌─────────────────────────┐       │
│  │      IndexedDB          │       │
│  │  - Cached responses     │       │
│  │  - Queued mutations     │       │
│  │  - Offline-created data │       │
│  └─────────────────────────┘       │
└─────────────────────────────────────┘
            ↕
┌─────────────────────────────────────┐
│        Service Worker                │
│  - Cache static assets (app shell)  │
│  - Cache API responses (GET)        │
│  - Background sync for mutations    │
│  - Push notifications               │
└─────────────────────────────────────┘
```

**What works offline:**

| Feature | Offline capability |
|---|---|
| Inspection creation | Full — checklist, photos, notes stored in IndexedDB, synced on reconnect |
| Toolbox talk delivery | Full — content pre-cached, signatures stored locally, synced on reconnect |
| Hazard report | Full — photo capture, voice note, form stored locally |
| Incident report | Full — voice note, photos, form stored locally |
| Morning brief | Read-only — last fetched brief is cached |
| Document viewing | Read-only — last viewed documents cached |
| Document generation | Not available offline (requires AI) |
| Mock inspection | Not available offline (requires AI) |
| Dashboard | Read-only — last fetched data displayed with stale indicator |

**Service worker cache strategy:**

| Resource type | Strategy |
|---|---|
| App shell (HTML, JS, CSS) | Cache-first, update in background |
| API GET responses | Network-first, fall back to cache |
| Images / photos | Cache-first (immutable after upload) |
| Font files | Cache-first (long TTL) |
| API mutations (POST/PATCH/DELETE) | Network-only, queue if offline |

### Camera integration

```typescript
// src/hooks/useCamera.ts

interface UseCameraOptions {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number;
  facingMode?: 'user' | 'environment';  // 'environment' = rear camera (default)
}

interface UseCameraReturn {
  capturePhoto: () => Promise<File | null>;
  isSupported: boolean;
  error: string | null;
}

export function useCamera(options: UseCameraOptions = {}): UseCameraReturn {
  const {
    maxWidth = 1920,
    maxHeight = 1920,
    quality = 0.8,
    facingMode = 'environment',
  } = options;

  const isSupported = 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices;

  const capturePhoto = async (): Promise<File | null> => {
    // Uses <input type="file" accept="image/*" capture="environment">
    // on mobile for native camera experience.
    // Falls back to getUserMedia on desktop.
    // Compresses result before returning.
  };

  return { capturePhoto, isSupported, error };
}
```

### Voice input integration

```typescript
// src/hooks/useVoiceInput.ts

interface UseVoiceInputOptions {
  language?: 'en-US' | 'es-MX';
  continuous?: boolean;
  interimResults?: boolean;
}

interface UseVoiceInputReturn {
  isRecording: boolean;
  transcript: string;
  interimTranscript: string;
  startRecording: () => void;
  stopRecording: () => void;
  resetTranscript: () => void;
  isSupported: boolean;
  audioBlob: Blob | null;          // raw audio for server-side transcription fallback
  error: string | null;
}

export function useVoiceInput(options: UseVoiceInputOptions = {}): UseVoiceInputReturn {
  // Primary: Web Speech API (SpeechRecognition)
  // Fallback: MediaRecorder API to capture audio, send to backend for transcription
  // The fallback is critical because Web Speech API is unreliable in
  // noisy construction environments. Server-side Whisper is more accurate.
}
```

### GPS/geolocation

```typescript
// src/hooks/useGeolocation.ts

interface UseGeolocationReturn {
  position: GeoPoint | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useGeolocation(): UseGeolocationReturn {
  // Requests position once on mount, caches for 5 minutes.
  // Used to auto-tag inspections, hazard reports, toolbox talks.
  // High accuracy mode for field use.
}
```

### Sunlight-readable design considerations

- High contrast ratios: minimum 7:1 for body text (WCAG AAA)
- Avoid light grays on white; use slate-700 minimum for text
- Status colors must be distinguishable beyond color alone (icons + text labels)
- Risk indicators use both color AND shape: green circle, yellow triangle, red octagon
- No translucent overlays or glass-morphism effects
- Font size minimum 16px on mobile (prevents iOS zoom and aids readability)
- Bold weight for important labels and values

### Low-bandwidth optimization

- Photo compression to max 200KB before upload (JPEG 80% quality, 1920px max dimension)
- Voice recordings compressed to Opus codec if available, MP3 fallback
- API responses paginated (20 items default, 50 max)
- List views show summaries; full detail fetched on tap
- React Query staleTime of 2 minutes reduces redundant fetches
- Service worker caches all static assets (< 1MB initial load target after compression)

---

## 7. INTERNATIONALIZATION (i18n)

### Architecture

The i18n system uses a JSON file-based approach with a custom lightweight hook. No heavy library (react-i18next is ~12KB gzipped) needed for two languages.

```typescript
// src/i18n/index.ts

type Locale = 'en' | 'es';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  formatDate: (date: string | Date) => string;
  formatNumber: (num: number) => string;
  formatCurrency: (amount: number) => string;
}
```

### Where translations live

```
src/i18n/locales/
├── en/
│   ├── common.json          # Shared: buttons, labels, navigation, errors
│   ├── dashboard.json       # Dashboard-specific strings
│   ├── inspections.json     # Inspection flow strings
│   ├── toolbox-talks.json   # Toolbox talk strings
│   ├── hazards.json         # Hazard reporting strings
│   ├── incidents.json       # Incident reporting strings
│   ├── workers.json         # Worker management strings
│   ├── equipment.json       # Equipment strings
│   ├── morning-brief.json   # Morning brief strings
│   └── settings.json        # Settings strings
└── es/
    └── (mirrors en/ exactly)
```

**Translation file format:**

```json
// en/common.json
{
  "nav.dashboard": "Dashboard",
  "nav.inspections": "Inspections",
  "nav.toolbox_talks": "Toolbox Talks",
  "btn.save": "Save",
  "btn.cancel": "Cancel",
  "btn.submit": "Submit",
  "btn.take_photo": "Take Photo",
  "btn.record_voice": "Record Voice Note",
  "status.online": "Online",
  "status.offline": "Offline — changes will sync when connected",
  "error.generic": "Something went wrong. Please try again.",
  "error.network": "No internet connection.",
  "date.today": "Today",
  "date.yesterday": "Yesterday"
}

// es/common.json
{
  "nav.dashboard": "Tablero",
  "nav.inspections": "Inspecciones",
  "nav.toolbox_talks": "Charlas de Seguridad",
  "btn.save": "Guardar",
  "btn.cancel": "Cancelar",
  "btn.submit": "Enviar",
  "btn.take_photo": "Tomar Foto",
  "btn.record_voice": "Grabar Nota de Voz",
  "status.online": "En linea",
  "status.offline": "Sin conexion — los cambios se sincronizaran al conectarse",
  "error.generic": "Algo salio mal. Intente de nuevo.",
  "error.network": "Sin conexion a internet.",
  "date.today": "Hoy",
  "date.yesterday": "Ayer"
}
```

### AI-generated content in both languages

AI-generated content (documents, toolbox talks, hazard analyses, morning briefs) is generated server-side in both languages simultaneously. The backend returns both `content_en` and `content_es` fields. The frontend displays based on the user's locale preference, with a toggle to switch.

```typescript
// Pattern for bilingual content display
interface BilingualContentProps {
  content_en: string;
  content_es: string;
  className?: string;
}

function BilingualContent({ content_en, content_es, className }: BilingualContentProps) {
  const { locale } = useLocale();
  const content = locale === 'es' ? content_es : content_en;

  return (
    <div className={className}>
      {content}
      <LanguageToggle />  {/* inline toggle to flip languages */}
    </div>
  );
}
```

### Number/date formatting

```typescript
// All formatting uses Intl API keyed to locale
const formatters = {
  en: {
    date: new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    number: new Intl.NumberFormat('en-US'),
    currency: new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }),
    time: new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }),
  },
  es: {
    date: new Intl.DateTimeFormat('es-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    number: new Intl.NumberFormat('es-US'),
    currency: new Intl.NumberFormat('es-US', { style: 'currency', currency: 'USD' }),
    time: new Intl.DateTimeFormat('es-US', { hour: 'numeric', minute: '2-digit' }),
  },
};
```

### RTL considerations

Not needed for en/es. If RTL languages are added in the future, the approach is:

- Use CSS logical properties (`margin-inline-start` instead of `margin-left`)
- Set `dir="rtl"` on the `<html>` element
- Tailwind v4 supports `rtl:` and `ltr:` variants

For now, no RTL code ships. The architecture supports it without rework.

---

## 8. COMPONENT ARCHITECTURE

### Design system principles

SafetyForge extends shadcn/ui with construction-safety-specific components. All primitives come from shadcn/ui. All business components compose shadcn primitives.

**Color system:**

| Token | Value | Usage |
|---|---|---|
| `orange-500` | `#f97316` | Primary brand, CTAs, active states |
| `orange-600` | `#ea580c` | Primary hover |
| `green-500` / `green-100` | | Compliant, pass, success |
| `amber-500` / `amber-100` | | At risk, warning, expiring soon |
| `red-500` / `red-100` | | Non-compliant, fail, critical, danger |
| `slate-800` | | Primary text |
| `slate-500` | | Secondary text |
| `slate-100` | | Borders, backgrounds |

### Shared component specifications

**DataTable**

```typescript
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  searchable?: boolean;
  searchPlaceholder?: string;
  filterOptions?: FilterOption[];
  sortable?: boolean;
  pageSize?: number;
  isLoading?: boolean;
  emptyState?: React.ReactNode;
  onRowClick?: (row: T) => void;
  // Mobile: renders as cards instead of table
  mobileCardRenderer?: (row: T) => React.ReactNode;
}
```

On mobile (< 768px), DataTable renders items as cards using `mobileCardRenderer`. No horizontal scrolling tables on phones.

**FormBuilder**

```typescript
interface FormBuilderProps {
  fields: TemplateField[];
  values: Record<string, string>;
  onChange: (fieldId: string, value: string) => void;
  errors?: Record<string, string>;
  disabled?: boolean;
  locale?: Language;
}
```

Renders dynamic forms from the existing `TemplateField` definitions in `constants.ts`. Used for document creation, inspection checklists, and any template-driven form.

**PhotoCapture**

```typescript
interface PhotoCaptureProps {
  onCapture: (file: File) => void;
  onAnalysis?: (analysis: HazardAiAnalysis) => void; // optional AI analysis
  maxPhotos?: number;
  existingPhotos?: Attachment[];
  disabled?: boolean;
}
```

Renders a camera button that opens native camera on mobile, file picker on desktop. Shows thumbnails of captured photos. Optionally sends to AI for hazard analysis.

**VoiceInput**

```typescript
interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onAudioBlob?: (blob: Blob) => void;
  language?: Language;
  placeholder?: string;
  maxDurationSeconds?: number;
}
```

Large record button (72px diameter) with pulse animation while recording. Shows real-time transcript below. Uses Web Speech API with server-side Whisper fallback.

**SignatureCapture**

```typescript
interface SignatureCaptureProps {
  onSign: (signatureDataUrl: string) => void;
  signerName: string;
  width?: number;
  height?: number;
}
```

Canvas-based touch signature pad. Used for toolbox talk sign-off. Renders signer name below the signature area. Saves as PNG data URL.

**ComplianceScoreCard**

```typescript
interface ComplianceScoreCardProps {
  score: number;              // 0-100
  previousScore?: number;     // for trend arrow
  label: string;
  size?: 'sm' | 'md' | 'lg';
}
```

Renders a circular progress ring with the score in the center. Color is green (80-100), amber (50-79), red (0-49). Shows up/down trend arrow if `previousScore` is provided.

**RiskBadge**

```typescript
interface RiskBadgeProps {
  level: RiskLevel;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

// Renders as:
// low     -> green circle + "Low"
// medium  -> yellow triangle + "Medium"
// high    -> orange diamond + "High"
// critical -> red octagon + "Critical"
```

Uses both color AND shape for sunlight readability and colorblind accessibility.

**OshaReference**

```typescript
interface OshaReferenceProps {
  code: string;           // e.g., "1926.502(d)"
  title?: string;
  summary?: string;
  variant?: 'inline' | 'card';
}
```

Inline variant renders as a styled code badge. Card variant renders as an expandable panel with the full standard text. Used throughout the app wherever OSHA citations appear.

---

## 9. PERFORMANCE

### Code splitting strategy

Every route is lazy-loaded. The initial bundle contains only:

- App shell (router, layout, providers): ~50KB gzipped
- shadcn/ui base components: ~30KB gzipped
- React + React DOM: ~45KB gzipped
- React Query: ~12KB gzipped
- Total initial load target: **< 150KB gzipped**

```typescript
// Route-based splitting (already shown in router.tsx)
const InspectionCreatePage = lazy(
  () => import('@/components/inspections/InspectionCreatePage')
);

// Component-level splitting for heavy components
const SignatureCapture = lazy(
  () => import('@/components/shared/SignatureCapture')
);
const RootCauseAnalysis = lazy(
  () => import('@/components/incidents/RootCauseAnalysis')
);
```

### Image optimization

- All uploaded photos compressed client-side before upload (1920px max, JPEG 80%, target < 200KB)
- Thumbnails generated server-side (200x200) and served for list views
- Images use `loading="lazy"` and `decoding="async"`
- Photo galleries use intersection observer to load on scroll

### Bundle size management

- Monitor with `npx vite-bundle-visualizer` on every PR
- Heavy libraries must be code-split (charting library loaded only on analytics pages)
- `date-fns` tree-shakes well; import individual functions, not the whole library
- No moment.js, lodash (full), or other heavy utilities

### Caching strategy

| Layer | What | TTL |
|---|---|---|
| Service worker | App shell (HTML, JS, CSS, fonts) | Until new version deployed |
| Service worker | API GET responses | 5 minutes (network-first) |
| Service worker | Uploaded images | Indefinite (content-addressed) |
| React Query | Server data | 2 minutes staleTime (configurable per query) |
| React Query | Morning brief | 30 minutes staleTime (generated daily) |
| IndexedDB | Offline mutations | Until synced |
| IndexedDB | Cached form data (drafts) | Until submitted |

### Prefetching strategy

```typescript
// Prefetch likely next pages on hover/focus
function ProjectCard({ project }: { project: ProjectSummary }) {
  const queryClient = useQueryClient();

  const prefetchProject = () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.projects.detail(project.id),
      queryFn: () => projectsApi.get(project.id),
      staleTime: 60_000,
    });
  };

  return (
    <Card
      onMouseEnter={prefetchProject}
      onFocus={prefetchProject}
    >
      {/* ... */}
    </Card>
  );
}
```

Prefetch rules:
- When a project card is hovered, prefetch that project's detail, morning brief, and recent inspections
- When the "New Inspection" button is visible, prefetch the checklist template
- When on a list page, prefetch the first 3 items' detail views

---

## 10. TESTING STRATEGY

### Framework choices

| Layer | Tool | Purpose |
|---|---|---|
| Unit tests | Vitest + Testing Library | Component rendering, hooks, utilities |
| Integration tests | Vitest + MSW | Component + API interaction |
| E2E tests | Playwright | Full user journeys |
| Visual regression | Playwright screenshots | Layout/style regression |
| Accessibility | axe-core + Playwright | WCAG compliance |

### Unit tests (Vitest + Testing Library)

Test categories per the CLAUDE.md conventions:

**UI tasks require:** RENDER, EMPTY, LOADING, ERROR_STATE, VALIDATION, SUBMIT, KEYBOARD, RESPONSIVE, DIRTY, DOUBLE_CLICK, OVERFLOW, ARIA

```typescript
// Example: InspectionCreatePage tests

describe('InspectionCreatePage', () => {
  // [RENDER] Renders checklist form with all required fields
  it('__CAT_RENDER renders checklist form with all sections', () => {});

  // [EMPTY] Shows empty state when no checklist template available
  it('__CAT_EMPTY shows message when no checklist template loaded', () => {});

  // [LOADING] Shows skeleton while checklist template loads
  it('__CAT_LOADING shows loading skeleton during fetch', () => {});

  // [ERROR_STATE] Shows error when checklist fetch fails
  it('__CAT_ERROR_STATE shows error message on API failure', () => {});

  // [VALIDATION] Prevents submit when required fields empty
  it('__CAT_VALIDATION blocks submit without required checklist items', () => {});

  // [SUBMIT] Submits inspection and navigates to detail page
  it('__CAT_SUBMIT creates inspection and redirects', () => {});

  // [KEYBOARD] Tab navigation through checklist items
  it('__CAT_KEYBOARD allows tab navigation through form', () => {});

  // [RESPONSIVE] Renders as card layout on mobile
  it('__CAT_RESPONSIVE renders mobile card layout below 768px', () => {});

  // [DIRTY] Warns before navigation with unsaved changes
  it('__CAT_DIRTY shows confirmation dialog on navigation with changes', () => {});

  // [DOUBLE_CLICK] Prevents double submission
  it('__CAT_DOUBLE_CLICK disables submit button during submission', () => {});

  // [ARIA] Form fields have correct aria labels
  it('__CAT_ARIA checklist items have accessible labels', () => {});
});
```

### Integration tests

Integration tests use MSW (Mock Service Worker) to mock API boundaries. Per CLAUDE.md, MSW is allowed for frontend integration tests (only IS-X and UJ-X ban mocks).

```typescript
// Test that inspection creation flow works end-to-end within the frontend
describe('Inspection creation integration', () => {
  it('[WIRING] submits inspection through API and updates cache', async () => {
    // MSW intercepts POST /projects/:id/inspections
    // Verifies correct payload, cache invalidation, navigation
  });
});
```

### E2E tests (Playwright)

Per CLAUDE.md, UJ-X tests MUST hit the real backend. No page.route(), no MSW.

```typescript
// e2e/journeys/foreman-daily-routine.spec.ts

test.describe('UJ-1: Foreman daily routine', () => {
  // [HAPPY_FLOW] Complete morning routine: brief -> toolbox talk -> inspection
  test('completes morning routine under 5 minutes', async ({ page }) => {
    // Login as foreman
    // View morning brief
    // Deliver toolbox talk with signature
    // Complete daily inspection with photo
    // Verify all records appear in dashboard
  });

  // [MESSY_FLOW] Handles intermittent connectivity during inspection
  test('completes inspection despite offline period', async ({ page }) => {
    // Start inspection
    // Go offline mid-checklist
    // Complete checklist offline
    // Go online
    // Verify sync completes
  });

  // [ERROR_RECOVERY] Recovers from failed photo upload
  test('retries failed photo upload', async ({ page }) => {});

  // [REPEAT_USE] Second inspection in same day works correctly
  test('creates multiple inspections same day same project', async ({ page }) => {});
});
```

### What to test for field-critical features

| Feature | Critical test scenarios |
|---|---|
| Offline inspection | Create offline, sync on reconnect, no data loss |
| Photo capture | Compression works, EXIF stripped, geo-tag attached |
| Voice input | Transcription populates text field, audio blob saved |
| Toolbox talk sign-off | Multiple signatures, all saved, timestamp correct |
| Hazard report | Photo + voice + form submit, AI analysis displayed |
| Language toggle | All strings switch, content switches, no flash |

### Accessibility testing

- Every page tested with axe-core in Playwright: zero violations
- Keyboard navigation tested for every form flow
- Screen reader tested for critical flows (inspection, hazard report)
- Color contrast tested against 7:1 ratio (AAA) for field readability
- Focus management tested on dialog open/close

---

## 11. BUILD ORDER

### What exists today

| Component | Status | Needs |
|---|---|---|
| `App.tsx` with routing | Working | Refactor to lazy loading, add project-scoped routes |
| `main.tsx` with providers | Working | Add I18n, Project, Offline providers |
| `api.ts` client | Working | Refactor to module structure with interceptors |
| `useAuth.ts` | Working | Minor: add language preference |
| `useDocuments.ts` | Working | Move to features/, add project scope |
| `DashboardPage.tsx` | Working | Expand with compliance overview, project cards |
| `DocumentCreatePage.tsx` | Working | Add project context, bilingual toggle |
| `DocumentEditPage.tsx` | Working | Add bilingual viewer, OSHA reference display |
| `LandingPage.tsx` | Working | Add ROI calculator, OSHA quiz entry point |
| `LoginPage.tsx` / `SignUpPage.tsx` | Working | Add language selector |
| `CompanySettingsPage.tsx` | Working | Add trades, employee count, safety officer |
| `BillingPage.tsx` | Working | Update tier names/pricing to match strategy |
| shadcn/ui components | Working | No changes needed |

### Phase 1 build order (Months 1-2)

**Sprint 1: Foundation refactoring (Week 1-2)**

1. Restructure `src/` into new folder layout (no behavior changes)
2. Refactor `api.ts` into `lib/api/` module with interceptors
3. Split `constants.ts` types into `types/models.ts`
4. Add `I18nProvider` with en/es JSON files for common strings
5. Add `ProjectProvider` and `ProjectPicker` component
6. Add `OfflineProvider` with basic connectivity detection
7. Implement `DataTable` shared component
8. Implement `FormBuilder` shared component

**Sprint 2: Project management (Week 3-4)**

9. `ProjectListPage` — list projects with compliance status
10. `ProjectCreatePage` — create project form
11. `ProjectDetailPage` — project hub with tabs
12. Update `DashboardPage` — multi-project compliance overview
13. Update sidebar navigation with project context
14. Implement mobile bottom tab bar

**Sprint 3: Daily inspection logs (Week 5-6)**

15. Define inspection checklist templates (JSON config per trade)
16. `InspectionCreatePage` — mobile-optimized checklist with photo
17. `InspectionListPage` — project-scoped list
18. `InspectionDetailPage` — read-only review with photos
19. `PhotoCapture` component with compression
20. Implement `useGeolocation` hook
21. Basic offline support for inspections (IndexedDB queue)

**Sprint 4: Toolbox talks (Week 7-8)**

22. `ToolboxTalkDeliverPage` — full-screen bilingual display
23. `ToolboxTalkSignOff` — crew signature collection
24. `SignatureCapture` component
25. `ToolboxTalkListPage` — project-scoped list
26. `ToolboxTalkDetailPage` — review with attendees
27. `LanguageToggle` component for bilingual content

**Sprint 5: Spanish language + JHA (Week 9-10)**

28. Complete all Spanish translation files
29. JHA generator — extend document create flow with JHA-specific fields
30. `BilingualContent` component for AI-generated content
31. `VoiceInput` component (Web Speech API + server fallback)
32. Update all existing pages with `t()` calls

**Sprint 6: Dashboard + OSHA 300 (Week 11-12)**

33. `ComplianceOverview` — red/yellow/green per project
34. `UpcomingDeadlines` — cert expirations, submission dates
35. `Osha300Page` — recordkeeping UI with auto-calculations
36. `UsageCard` — subscription tier and limits
37. `RecentActivity` — cross-project activity feed

### Phase 2 build order (Months 3-4)

**Sprint 7: Morning brief + Hazard reporting**

38. `MorningBriefPage` — risk score, alerts, weather, actions
39. `RiskScoreDisplay` component (animated ring)
40. `HazardReportPage` — photo + voice + AI analysis
41. `HazardAnalysisCard` — AI analysis display with OSHA refs
42. `OshaReference` component
43. `useCamera` hook with rear-camera default
44. `useVoiceInput` hook with Whisper fallback

**Sprint 8: Mock OSHA inspection**

45. `MockInspectionPage` — trigger inspection flow
46. `MockInspectionResults` — citation-format findings
47. `FindingCard` — individual finding with severity, citation, action
48. `ComplianceScoreCard` component
49. `MockInspectionHistory` — trend over time

**Sprint 9: Worker management + Certifications**

50. `WorkerListPage` with certification status badges
51. `WorkerDetailPage` with certification cards
52. `CertificationCard` with expiry countdown
53. `TrainingMatrix` — grid view of workers x certifications
54. `ExpirationAlerts` — filtered list of upcoming expirations

**Sprint 10: Incident management**

55. `IncidentReportPage` — voice-first incident capture
56. `IncidentDetailPage` with timeline
57. `IncidentTimeline` component
58. `RootCauseAnalysis` — guided 5-Why flow
59. `TimelineView` shared component
60. OSHA 301 auto-generation from incident data

**Sprint 11: Analytics + EMR modeling**

61. `AnalyticsDashboard` — charts, trends, KPIs
62. `EmrModelingPage` — EMR impact calculator with dollar amounts
63. `TrendCharts` — line charts for compliance, incidents, inspections
64. Add charting library (recharts or chart.js — code-split)

**Sprint 12: Voice input + Equipment + Polish**

65. Equipment management pages (list, detail, inspection)
66. Voice input integration across all report forms
67. Full offline support audit and fixes
68. Performance optimization (bundle analysis, prefetching)
69. Accessibility audit and fixes

### Dependencies between features

```
Project management ──→ (all project-scoped features depend on this)
    ├── Inspections
    ├── Toolbox Talks
    ├── Hazard Reports
    ├── Incidents
    ├── Morning Brief
    └── Equipment (project-scoped inspections)

I18n framework ──→ (all UI depends on this for bilingual)
    └── All components use t() for strings

Offline framework ──→ (field features depend on this)
    ├── Inspections
    ├── Toolbox Talks
    ├── Hazard Reports
    └── Incidents

PhotoCapture component ──→
    ├── Inspections (photo evidence)
    ├── Hazard Reports (photo analysis)
    └── Equipment inspections

VoiceInput component ──→
    ├── Hazard Reports (voice notes)
    ├── Incident Reports (voice capture)
    └── Inspection notes

SignatureCapture component ──→
    └── Toolbox Talk sign-off

Worker management ──→
    ├── Certification tracking
    ├── Training matrix
    ├── Toolbox talk attendees
    └── Morning brief (cert warnings)

DataTable component ──→ (all list pages)
FormBuilder component ──→ (all create/edit pages)
```

### Phase 3-4 features (Months 5-12, planned but not detailed)

- Prequalification automation (ISN/Avetta form auto-fill)
- Predictive risk scoring (ML-powered morning briefs)
- GC/Sub portal (separate dashboard for GC users)
- EMR insurance integration
- State-specific compliance engine (Cal/OSHA overlay)
- API/webhook integration settings
- Environmental compliance module

These features are designed at the architecture level (routes, types, API modules exist) but implementation details are deferred to their respective spec documents.

---

## APPENDIX A: Key architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| State management | React Query + Context only | No Redux/Zustand needed; server state dominates |
| Routing | React Router v6 | Already in use, sufficient for the route complexity |
| i18n | Custom lightweight hook + JSON files | Only 2 languages, no need for heavy library |
| Offline storage | IndexedDB via idb library | Structured data storage, better than localStorage |
| Service worker | Workbox (via vite-plugin-pwa) | Production-ready caching strategies |
| Charting | recharts (lazy-loaded) | React-native charts, tree-shakeable |
| Forms | Controlled components (no form library) | Forms are simple checklists, not complex multi-step |
| Photo compression | browser-image-compression | Client-side, reduces upload size 10x |
| Signature | react-signature-canvas | Lightweight, touch-optimized |
| Date formatting | date-fns + Intl API | Tree-shakeable, locale-aware |

## APPENDIX B: Environment variables

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_STRIPE_PUBLISHABLE_KEY=
VITE_SENTRY_DSN=
VITE_APP_VERSION=
```
