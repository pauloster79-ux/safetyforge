import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublicRoute } from '@/components/auth/PublicRoute';
import { LoginPage } from '@/components/auth/LoginPage';
import { SignUpPage } from '@/components/auth/SignUpPage';
import { ForgotPasswordPage } from '@/components/auth/ForgotPasswordPage';
import { SsoCallbackPage } from '@/components/auth/SsoCallbackPage';
import { LandingPage } from '@/components/landing/LandingPage';
import { CompanyOnboarding } from '@/components/onboarding/CompanyOnboarding';
import { DashboardPage } from '@/components/dashboard/DashboardPage';
import { DocumentListPage } from '@/components/documents/DocumentListPage';
import { DocumentCreatePage } from '@/components/documents/DocumentCreatePage';
import { DocumentEditPage } from '@/components/documents/DocumentEditPage';
import { TemplatePickerPage } from '@/components/templates/TemplatePickerPage';
import { CompanySettingsPage } from '@/components/company/CompanySettingsPage';
import { BillingPage } from '@/components/billing/BillingPage';
import { ProjectListPage } from '@/components/projects/ProjectListPage';
import { ProjectCreatePage } from '@/components/projects/ProjectCreatePage';
import { ProjectDetailPage } from '@/components/projects/ProjectDetailPage';
import { InspectionListPage } from '@/components/inspections/InspectionListPage';
import { InspectionCreatePage } from '@/components/inspections/InspectionCreatePage';
import { InspectionDetailPage } from '@/components/inspections/InspectionDetailPage';
import { ToolboxTalkListPage } from '@/components/toolbox-talks/ToolboxTalkListPage';
import { ToolboxTalkCreatePage } from '@/components/toolbox-talks/ToolboxTalkCreatePage';
import { ToolboxTalkDeliverPage } from '@/components/toolbox-talks/ToolboxTalkDeliverPage';
import { ToolboxTalkDetailPage } from '@/components/toolbox-talks/ToolboxTalkDetailPage';
import { WorkerListPage } from '@/components/workers/WorkerListPage';
import { WorkerCreatePage } from '@/components/workers/WorkerCreatePage';
import { WorkerDetailPage } from '@/components/workers/WorkerDetailPage';
import { CertificationMatrixPage } from '@/components/workers/CertificationMatrixPage';
import { OshaLogPage } from '@/components/osha-log/OshaLogPage';
import { MockInspectionPage } from '@/components/mock-inspection/MockInspectionPage';
import { HazardReportPage } from '@/components/hazards/HazardReportPage';
import { MorningBriefPage } from '@/components/morning-brief/MorningBriefPage';
import { IncidentListPage } from '@/components/incidents/IncidentListPage';
import { IncidentCreatePage } from '@/components/incidents/IncidentCreatePage';
import { IncidentDetailPage } from '@/components/incidents/IncidentDetailPage';
import { AnalyticsPage } from '@/components/analytics/AnalyticsPage';
import { PrequalificationPage } from '@/components/prequalification/PrequalificationPage';
import { GcPortalPage } from '@/components/gc-portal/GcPortalPage';
import { StateCompliancePage } from '@/components/state-compliance/StateCompliancePage';
import { EnvironmentalPage } from '@/components/environmental/EnvironmentalPage';
import { EquipmentPage } from '@/components/equipment/EquipmentPage';
import { EquipmentCreatePage } from '@/components/equipment/EquipmentCreatePage';
import { EquipmentDetailPage } from '@/components/equipment/EquipmentDetailPage';
import { TeamMembersPage } from '@/components/team/TeamMembersPage';

export function App() {
  return (
    <ErrorBoundary>
    <BrowserRouter>
      <Routes>
        {/* Public routes — redirect to dashboard if already authenticated */}
        <Route
          path="/"
          element={
            <PublicRoute fallback={<Navigate to="/dashboard" replace />}>
              <LandingPage />
            </PublicRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute fallback={<Navigate to="/dashboard" replace />}>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/signup"
          element={
            <PublicRoute fallback={<Navigate to="/dashboard" replace />}>
              <SignUpPage />
            </PublicRoute>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <PublicRoute fallback={<Navigate to="/dashboard" replace />}>
              <ForgotPasswordPage />
            </PublicRoute>
          }
        />

        {/* Clerk SSO callback route */}
        <Route path="/sso-callback" element={<SsoCallbackPage />} />

        {/* Onboarding — protected but outside AppLayout */}
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <CompanyOnboarding />
            </ProtectedRoute>
          }
        />

        {/* Protected routes — require authentication */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectListPage />} />
          <Route path="/projects/new" element={<ProjectCreatePage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/inspections/new" element={<InspectionCreatePage />} />
          <Route path="/projects/:projectId/inspections/:inspectionId" element={<InspectionDetailPage />} />
          <Route path="/projects/:projectId/toolbox-talks/new" element={<ToolboxTalkCreatePage />} />
          <Route path="/projects/:projectId/toolbox-talks/:talkId/deliver" element={<ToolboxTalkDeliverPage />} />
          <Route path="/projects/:projectId/toolbox-talks/:talkId" element={<ToolboxTalkDetailPage />} />
          <Route path="/projects/:projectId/hazard-report/new" element={<HazardReportPage />} />
          <Route path="/projects/:projectId/hazard-reports/:id" element={<HazardReportPage />} />
          <Route path="/projects/:projectId/morning-brief" element={<MorningBriefPage />} />
          <Route path="/projects/:projectId/incidents/new" element={<IncidentCreatePage />} />
          <Route path="/projects/:projectId/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/inspections" element={<InspectionListPage />} />
          <Route path="/incidents" element={<IncidentListPage />} />
          <Route path="/toolbox-talks" element={<ToolboxTalkListPage />} />
          <Route path="/workers" element={<WorkerListPage />} />
          <Route path="/workers/new" element={<WorkerCreatePage />} />
          <Route path="/workers/certification-matrix" element={<CertificationMatrixPage />} />
          <Route path="/workers/:workerId" element={<WorkerDetailPage />} />
          <Route path="/osha-log" element={<OshaLogPage />} />
          <Route path="/mock-inspection" element={<MockInspectionPage />} />
          <Route path="/mock-inspection/results/:id" element={<MockInspectionPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/prequalification" element={<PrequalificationPage />} />
          <Route path="/gc-portal" element={<GcPortalPage />} />
          <Route path="/state-compliance" element={<StateCompliancePage />} />
          <Route path="/environmental" element={<EnvironmentalPage />} />
          <Route path="/equipment" element={<EquipmentPage />} />
          <Route path="/equipment/new" element={<EquipmentCreatePage />} />
          <Route path="/equipment/:equipmentId" element={<EquipmentDetailPage />} />
          <Route path="/documents" element={<DocumentListPage />} />
          <Route path="/documents/new" element={<DocumentCreatePage />} />
          <Route path="/documents/:id" element={<DocumentEditPage />} />
          <Route path="/templates" element={<TemplatePickerPage />} />
          <Route path="/settings" element={<CompanySettingsPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/team" element={<TeamMembersPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </ErrorBoundary>
  );
}
