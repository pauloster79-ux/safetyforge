import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { AppShell } from '@/components/shell/AppShell';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublicRoute } from '@/components/auth/PublicRoute';
import { LoginPage } from '@/components/auth/LoginPage';
import { SignUpPage } from '@/components/auth/SignUpPage';
import { ForgotPasswordPage } from '@/components/auth/ForgotPasswordPage';
import { SsoCallbackPage } from '@/components/auth/SsoCallbackPage';
import { LandingPage } from '@/components/landing/LandingPage';
import { CompanyOnboarding } from '@/components/onboarding/CompanyOnboarding';
import VoiceInspectionPage from '@/components/voice-inspection/VoiceInspectionPage';

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

        {/* Onboarding — protected but outside AppShell */}
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <CompanyOnboarding />
            </ProtectedRoute>
          }
        />

        {/* Voice inspection — full-screen, outside AppShell */}
        <Route
          path="/projects/:projectId/inspect/voice"
          element={
            <ProtectedRoute>
              <VoiceInspectionPage />
            </ProtectedRoute>
          }
        />

        {/* All protected routes — conversational-first shell */}
        {/* The AppShell handles navigation internally via canvas state */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
    </ErrorBoundary>
  );
}
