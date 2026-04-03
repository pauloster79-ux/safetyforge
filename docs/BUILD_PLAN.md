# SafetyForge Build Plan

*Version 1.0 -- 2026-03-31*

---

## OVERVIEW

This document is the execution plan for SafetyForge from its current broken state to a revenue-generating product. It synthesizes four architecture documents (backend, frontend, infrastructure, product strategy) and a critical codebase audit into a sprint-by-sprint implementation guide. The current codebase has a working frontend shell with demo mode, a backend with document generation via Claude, and Firebase/Firestore infrastructure -- but the two halves do not talk to each other due to API path mismatches, data model mismatches, and missing entities. The goal is Phase 1 (paying customers) in 6 weeks and Phase 2 (intelligence layer) in 12 weeks.

---

## CRITICAL PATH

The shortest path to revenue:

1. **Fix the frontend-backend contract** so a single API call actually works (Sprint 0).
2. **Add the Project entity** that every downstream feature depends on (Sprint 2).
3. **Ship daily-use features** (inspections, toolbox talks) that justify a monthly subscription (Sprints 2-3).
4. **Enable billing** with the correct per-project pricing model (Sprint 1).
5. **Ship the killer feature** (Mock OSHA Inspection) that converts Professional tier upgrades (Sprint 6).

Nothing else matters until step 1 is complete. A user who signs up, creates a document, and gets a 404 will never come back.

---

## SPRINT PLAN

---

### Sprint 0: Foundation Fix (Week 1)

**Goal:** Make the existing frontend talk to the existing backend -- one user can sign up, create a company, generate a document, and view it.

#### S0-T1: Unify API path convention

- **What:** The frontend calls flat paths (`/documents`, `/documents/:id`). The backend expects nested paths (`/companies/{company_id}/documents`). Fix the frontend API client to inject `company_id` into every request path automatically.
- **Files to modify:**
  - `frontend/src/lib/api.ts` -- Add `companyId` to the API client state; create a `companyApi` wrapper that auto-prefixes `/companies/{companyId}` to all paths.
  - `frontend/src/hooks/useDocuments.ts` -- Update all endpoint strings from `/documents` to use the company-prefixed client.
  - `frontend/src/hooks/useCompany.ts` -- Update endpoint strings.
  - `frontend/src/components/billing/BillingPage.tsx` -- Update endpoint strings.
- **Dependency:** None (first task).
- **Effort:** 4 hours.

#### S0-T2: Align document type IDs between frontend and backend

- **What:** Frontend uses `safety_plan`, `emergency_plan`, `incident_report`. Backend uses `sssp`, `fall_protection`, `hazcom`, etc. Create a mapping layer and update the frontend constants.
- **Files to modify:**
  - `frontend/src/lib/constants.ts` -- Change `DOCUMENT_TYPES` array: rename `safety_plan` to `sssp`, `emergency_plan` to keep as-is but add backend mapping, add `fall_protection`. Keep `jha`, `toolbox_talk`, `incident_report` which already match.
  - `backend/app/models/document.py` -- Add any missing types to the `DocumentType` enum (add `emergency_action_plan` to match frontend's `emergency_plan`).
- **Dependency:** None.
- **Effort:** 2 hours.

#### S0-T3: Align document content structure

- **What:** Frontend expects `content.sections[]` where each section is `{id, title, content: string}`. Backend generation service produces structured JSON with nested objects, arrays, and dicts. Fix the backend generation service to output the `sections[]` format the frontend expects.
- **Files to modify:**
  - `backend/app/services/generation_service.py` -- Modify the AI prompt to request output in `{sections: [{id, title, content}]}` format. Add a post-processing function `_normalize_content(raw_content: dict) -> dict` that flattens any nested structure into the sections format.
  - `frontend/src/lib/constants.ts` -- Verify `DocumentContent` and `DocumentSection` interfaces match the backend output. No change expected.
- **Dependency:** None.
- **Effort:** 4 hours.

#### S0-T4: Align Company model fields

- **What:** Frontend `Company` interface references `ein`, `safety_officer`, `safety_officer_phone` which exist in the architecture spec but may not be exposed by the current backend API. Backend `CompanyCreate` model has `owner_name`, `trade_type` which frontend does not send.
- **Files to modify:**
  - `backend/app/models/company.py` -- Add optional fields to the `Company` response model: `ein: str | None`, `safety_officer: str | None`, `safety_officer_phone: str | None`, `safety_officer_email: str | None`, `employee_count: int | None`, `logo_url: str | None`. Update `CompanyCreate` to make `ein`, `safety_officer*` fields optional.
  - `frontend/src/lib/constants.ts` -- Update `Company` interface: change `subscription_tier` from `'free' | 'pro' | 'enterprise'` to `'starter' | 'professional' | 'business' | 'enterprise'`. Add `owner_name`, `trade_type` fields. Make `ein`, `safety_officer`, `safety_officer_phone` optional with `?`.
  - `frontend/src/components/company/CompanySettingsPage.tsx` -- Update form fields to match the aligned model.
- **Dependency:** None.
- **Effort:** 3 hours.

#### S0-T5: Fix subscription/pricing tier mismatch

- **What:** Three different pricing structures exist: frontend has `free/$49/$149` per-document tiers; product strategy has `$99/$299/$599` per-project tiers; backend has Lemon Squeezy integration with unknown tier IDs. Align everything to the product strategy pricing.
- **Files to modify:**
  - `frontend/src/lib/constants.ts` -- Replace `SUBSCRIPTION_TIERS` array with the product strategy tiers: Starter ($99/mo, 2 projects), Professional ($299/mo, 8 projects), Business ($599/mo, 20 projects). Remove `monthlyLimit` (document-based), add `projectLimit`.
  - `frontend/src/components/landing/LandingPage.tsx` -- Update pricing section to reflect new tiers.
  - `frontend/src/components/billing/BillingPage.tsx` -- Update tier display and upgrade flow.
  - `backend/app/models/billing.py` -- Verify tier IDs match: `starter`, `professional`, `business`, `enterprise`.
  - `backend/app/services/billing_service.py` -- Update tier-to-limit mapping to use project counts instead of document counts.
- **Dependency:** S0-T4 (Company model changes).
- **Effort:** 4 hours.

#### S0-T6: Add GET /documents/stats endpoint

- **What:** The frontend dashboard calls `GET /documents/stats` which does not exist. Add it to the backend.
- **Files to modify:**
  - `backend/app/routers/documents.py` -- Add endpoint `GET /companies/{company_id}/documents/stats` that returns `{total: int, by_type: dict, by_status: dict, this_month: int}`.
  - `backend/app/services/document_service.py` -- Add method `get_stats(company_id: str) -> DocumentStats` that queries Firestore for aggregate counts.
  - `backend/app/models/document.py` -- Add `DocumentStats` response model.
  - `frontend/src/hooks/useDocuments.ts` -- Update the stats endpoint path to use company-prefixed path.
- **Dependency:** S0-T1 (API path fix).
- **Effort:** 3 hours.

#### S0-T7: Fix async/sync Firestore mismatch

- **What:** The FastAPI endpoints are async (`async def`) but the Firestore client uses synchronous calls (`.get()`, `.set()`, `.stream()`). This blocks the event loop. Wrap Firestore calls in `asyncio.to_thread()` or use `run_in_executor`.
- **Files to modify:**
  - `backend/app/services/document_service.py` -- Wrap all Firestore `.get()`, `.set()`, `.update()`, `.stream()` calls in `await asyncio.to_thread(...)`.
  - `backend/app/services/company_service.py` -- Same treatment.
  - `backend/app/services/generation_service.py` -- Same treatment for Firestore calls (Anthropic SDK is already async).
  - `backend/app/services/template_service.py` -- Same treatment.
  - `backend/app/services/billing_service.py` -- Same treatment.
- **Dependency:** None.
- **Effort:** 4 hours.

#### S0-T8: Fix service instantiation per request

- **What:** Services are created inside each route handler (`DocumentService(db)` on every request). Move to FastAPI dependency injection with singleton services.
- **Files to modify:**
  - `backend/app/dependencies.py` -- Add dependency functions: `get_document_service()`, `get_company_service()`, `get_generation_service()`, `get_template_service()`, `get_billing_service()`. Each returns a cached singleton.
  - `backend/app/routers/documents.py` -- Replace inline `DocumentService(db)` with `Depends(get_document_service)`.
  - `backend/app/routers/companies.py` -- Same pattern.
  - `backend/app/routers/billing.py` -- Same pattern.
  - `backend/app/routers/templates.py` -- Same pattern.
  - `backend/app/routers/pdf.py` -- Same pattern.
- **Dependency:** None.
- **Effort:** 3 hours.

#### S0-T9: Fix Cloud Run region (europe-west2 to us-central1)

- **What:** Deploy script targets `europe-west2` (London) but target market is US contractors. Change to `us-central1`.
- **Files to modify:**
  - `backend/deploy.sh` -- Change `REGION="europe-west2"` to `REGION="us-central1"`.
  - `docs/architecture/INFRASTRUCTURE.md` -- Update region references from `europe-west2` to `us-central1` (Section 3.1).
- **Dependency:** None.
- **Effort:** 0.5 hours.

#### S0-T10: Add pagination to document listing

- **What:** Document list endpoint returns all documents with no pagination. Add cursor-based pagination.
- **Files to modify:**
  - `backend/app/models/document.py` -- Add `PaginatedResponse` model with `items: list[Document]`, `next_cursor: str | None`, `has_more: bool`.
  - `backend/app/services/document_service.py` -- Modify `list_documents()` to accept `limit: int = 20`, `cursor: str | None = None`. Use Firestore `start_after()` with the cursor document.
  - `backend/app/routers/documents.py` -- Add `?limit=20&cursor=xxx` query params to GET list endpoint.
  - `frontend/src/hooks/useDocuments.ts` -- Update to use React Query's `useInfiniteQuery` with cursor-based pagination.
- **Dependency:** S0-T1, S0-T8.
- **Effort:** 4 hours.

#### S0-T11: Set up test infrastructure

- **What:** Zero tests exist. Set up backend pytest with Firestore emulator and frontend Vitest.
- **Files to create:**
  - `backend/tests/__init__.py`
  - `backend/tests/conftest.py` -- Firestore emulator fixture, test settings, test client fixture.
  - `backend/tests/test_document_service.py` -- 3 smoke tests: create, get, list.
  - `backend/tests/test_company_service.py` -- 2 smoke tests: create, get.
  - `backend/pytest.ini` or `backend/pyproject.toml` -- pytest config with asyncio mode.
  - `frontend/vitest.config.ts` -- Vitest config with React Testing Library.
  - `frontend/src/__tests__/api.test.ts` -- Smoke test for API client (demo mode).
- **Files to modify:**
  - `backend/requirements.txt` or `backend/pyproject.toml` -- Add `pytest`, `pytest-asyncio`, `httpx` (for TestClient).
  - `frontend/package.json` -- Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`.
  - `docker-compose.yml` -- Add Firestore emulator service if not present.
- **Dependency:** None.
- **Effort:** 6 hours.

**Sprint 0 Definition of Done:**
- A real (non-demo) user can: sign up with Firebase Auth, create a company, generate a safety document (SSSP), view the generated document with rendered sections, see document stats on the dashboard.
- All API calls from frontend hit backend endpoints and return 200.
- Backend tests pass against Firestore emulator.
- Frontend smoke tests pass.
- No 404s in the network tab during the happy path.

**Sprint 0 Total Estimated Effort:** 37.5 hours (~1 week at full capacity)

---

### Sprint 1: Core Integration (Week 2)

**Goal:** Full CRUD flow for documents works end-to-end with real auth; demo mode becomes the fallback, not the primary experience.

#### S1-T1: Implement onboarding wizard

- **What:** After signup, guide the user through company creation with the correct fields (trade type, employee count, address, license number). Currently there is no onboarding flow -- user lands on an empty dashboard.
- **Files to create:**
  - `frontend/src/components/auth/OnboardingWizard.tsx` -- Multi-step form: Company Info (name, address, phone, email, license_number, trade_type) -> Safety Info (employee_count, safety_officer_name) -> Done. Calls `POST /api/v1/auth/signup` with company data.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add `/onboarding` route. Redirect to onboarding if user has no company_id.
  - `frontend/src/hooks/useAuth.ts` -- Add `companyId` to auth state. Check for company association on login.
  - `backend/app/routers/auth.py` -- Verify `POST /auth/signup` creates both user association and company. Return `company_id` in response.
- **Dependency:** S0-T1, S0-T4.
- **Effort:** 8 hours.

#### S1-T2: Wire up React Query for all existing features

- **What:** Replace direct `api.get()` calls with React Query hooks for caching, loading states, and error handling.
- **Files to create:**
  - `frontend/src/lib/query-keys.ts` -- Query key factory (documents, company, subscription keys only for now).
  - `frontend/src/lib/api/client.ts` -- Refactored API client with company-aware base path.
- **Files to modify:**
  - `frontend/src/hooks/useDocuments.ts` -- Rewrite to use `useQuery` and `useMutation` from `@tanstack/react-query`.
  - `frontend/src/hooks/useCompany.ts` -- Same rewrite.
  - `frontend/src/main.tsx` -- Add `QueryClientProvider`.
  - `frontend/src/components/documents/DocumentListPage.tsx` -- Use loading/error states from the hook.
  - `frontend/src/components/dashboard/DashboardPage.tsx` -- Use React Query hooks.
- **Dependency:** S0-T1, S0-T6.
- **Effort:** 8 hours.

#### S1-T3: Document generation end-to-end with progress indicator

- **What:** Document generation takes 30-60 seconds. Add a streaming/polling progress indicator. Currently the frontend fires POST and hopes for the best.
- **Files to modify:**
  - `backend/app/routers/documents.py` -- Add `POST /companies/{cid}/documents/generate` endpoint that returns `202 Accepted` with a `generation_id`, then the client polls `GET /companies/{cid}/documents/{id}` for status changes.
  - `backend/app/services/generation_service.py` -- Set document status to `generating` before starting AI call, `draft` on completion, `generation_failed` on error.
  - `frontend/src/components/documents/DocumentCreatePage.tsx` -- After submitting, show a progress screen that polls the document status every 2 seconds until `status !== 'generating'`.
  - `frontend/src/hooks/useDocuments.ts` -- Add `useDocumentGeneration` hook with polling via React Query's `refetchInterval`.
- **Dependency:** S0-T3, S0-T7.
- **Effort:** 6 hours.

#### S1-T4: Document edit and section editing

- **What:** The DocumentEditPage exists but needs to work with the aligned content structure. Verify section editing saves back to backend.
- **Files to modify:**
  - `frontend/src/components/documents/DocumentEditPage.tsx` -- Ensure it reads `content.sections[]`, renders each section's `content` as editable text, and calls `PATCH /companies/{cid}/documents/{id}` on save.
  - `backend/app/routers/documents.py` -- Verify `PATCH` endpoint accepts partial `content` updates.
- **Dependency:** S0-T2, S0-T3.
- **Effort:** 4 hours.

#### S1-T5: PDF export end-to-end

- **What:** Wire up PDF generation. Backend has `pdf_service.py` with WeasyPrint. Frontend has no PDF download button that actually works.
- **Files to modify:**
  - `frontend/src/components/documents/DocumentEditPage.tsx` -- Add "Export PDF" button that calls `POST /companies/{cid}/documents/{id}/pdf` and then downloads the file.
  - `backend/app/routers/pdf.py` -- Verify it returns the PDF binary with correct Content-Type headers. Add the company-scoped path if needed.
  - `backend/app/services/pdf_service.py` -- Verify it handles the normalized `sections[]` content format.
- **Dependency:** S0-T3 (content structure fix).
- **Effort:** 4 hours.

#### S1-T6: Billing integration with Lemon Squeezy

- **What:** Wire up the checkout flow so users can subscribe. Update the billing page to use the product strategy tiers.
- **Files to modify:**
  - `backend/app/services/billing_service.py` -- Map Lemon Squeezy product IDs to `starter`, `professional`, `business` tiers. Update `create_checkout()` to accept tier parameter.
  - `backend/app/routers/billing.py` -- Update `POST /companies/{cid}/billing/checkout` to accept `{tier: string}`.
  - `frontend/src/components/billing/BillingPage.tsx` -- Show the three tiers with correct pricing. Checkout button calls the backend which returns a Lemon Squeezy checkout URL. Redirect to that URL.
  - `backend/app/routers/billing.py` -- Verify webhook handler updates `subscription_tier` and `max_active_projects` on the company document.
- **Dependency:** S0-T5 (pricing alignment).
- **Effort:** 6 hours.

#### S1-T7: Error handling and loading states

- **What:** Add consistent error boundaries, loading skeletons, and empty states across all pages.
- **Files to create:**
  - `frontend/src/components/shared/ErrorBoundary.tsx` -- React error boundary with retry button.
  - `frontend/src/components/shared/LoadingSkeleton.tsx` -- Reusable skeleton components for cards, lists, forms.
  - `frontend/src/components/shared/EmptyState.tsx` -- Reusable empty state with icon, title, description, CTA button.
- **Files to modify:**
  - `frontend/src/components/documents/DocumentListPage.tsx` -- Add loading skeleton and empty state.
  - `frontend/src/components/dashboard/DashboardPage.tsx` -- Add loading skeleton.
  - `frontend/src/App.tsx` -- Wrap authenticated routes in ErrorBoundary.
- **Dependency:** S1-T2.
- **Effort:** 4 hours.

**Sprint 1 Definition of Done:**
- New user can: sign up, complete onboarding, see empty dashboard, create and generate a document, edit sections, export to PDF, view billing page with real tiers.
- Demo mode still works for unauthenticated users.
- All pages show proper loading, error, and empty states.
- React Query manages all server state.

**Sprint 1 Total Estimated Effort:** 40 hours

---

### Sprint 2: Project Entity + Inspections (Week 3)

**Goal:** Add the Project model so documents, inspections, and all future features are project-scoped. Ship daily inspection logs.

#### S2-T1: Backend -- Project model and service

- **What:** Create the Project entity in Firestore as a subcollection of companies. Full CRUD.
- **Files to create:**
  - `backend/app/models/project.py` -- `ProjectCreate`, `ProjectUpdate`, `Project`, `ProjectStatus` enum (`active`, `on_hold`, `completed`, `archived`), `ProjectType` enum.
  - `backend/app/services/project_service.py` -- `ProjectService` with methods: `create()`, `get()`, `list_projects()`, `update()`, `delete()` (soft), `update_compliance_score()`. Collection path: `companies/{cid}/projects/{pid}`.
  - `backend/app/routers/projects.py` -- CRUD endpoints under `/companies/{cid}/projects`. Include `GET .../compliance` for project compliance summary.
- **Files to modify:**
  - `backend/app/main.py` -- Register the projects router.
  - `backend/app/dependencies.py` -- Add `get_project_service()` singleton.
- **Dependency:** S0-T8 (DI pattern).
- **Effort:** 8 hours.

#### S2-T2: Backend -- Migrate documents to project scope

- **What:** Documents become a subcollection of projects: `companies/{cid}/projects/{pid}/documents/{did}`. Maintain backward compatibility with existing company-level documents.
- **Files to modify:**
  - `backend/app/services/document_service.py` -- Add `project_id` parameter to all methods. Change Firestore collection path from `companies/{cid}/documents` to `companies/{cid}/projects/{pid}/documents`. Add a fallback that checks company-level documents for backward compatibility.
  - `backend/app/routers/documents.py` -- Update prefix to `/companies/{company_id}/projects/{project_id}/documents`. Keep the old route as a redirect/alias during migration.
  - `backend/app/models/document.py` -- Add `project_id: str` to `Document` model and `DocumentCreate`.
- **Dependency:** S2-T1.
- **Effort:** 6 hours.

#### S2-T3: Frontend -- Project management pages

- **What:** Build project list, create, and detail pages.
- **Files to create:**
  - `frontend/src/components/projects/ProjectListPage.tsx` -- Card grid of projects with status badges (green/yellow/red compliance), "New Project" CTA.
  - `frontend/src/components/projects/ProjectCreatePage.tsx` -- Form: name, address, project type, start/end dates, scope of work, GC info, nearest hospital.
  - `frontend/src/components/projects/ProjectDetailPage.tsx` -- Project hub with tabs: Overview, Documents, Inspections, Toolbox Talks.
  - `frontend/src/features/projects/useProjects.ts` -- React Query hooks for project CRUD.
  - `frontend/src/lib/api/resources/projects.api.ts` -- API functions for project endpoints.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes: `/projects`, `/projects/new`, `/projects/:projectId`.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add "Projects" nav item.
  - `frontend/src/lib/constants.ts` -- Add Project-related types and ROUTES entries.
  - `frontend/src/lib/query-keys.ts` -- Add project query keys.
- **Dependency:** S2-T1 (backend must exist), S1-T2 (React Query).
- **Effort:** 10 hours.

#### S2-T4: Frontend -- Update document flow to be project-scoped

- **What:** Document creation now requires selecting (or being within) a project. Update the document list to show per-project documents.
- **Files to modify:**
  - `frontend/src/components/documents/DocumentListPage.tsx` -- Accept `projectId` from URL params. Filter documents by project.
  - `frontend/src/components/documents/DocumentCreatePage.tsx` -- Require `projectId`. Pre-fill project info into the generation form.
  - `frontend/src/hooks/useDocuments.ts` -- All endpoints now include `projectId` in the path.
  - `frontend/src/App.tsx` -- Add project-scoped document routes: `/projects/:projectId/documents`, `/projects/:projectId/documents/new`, `/projects/:projectId/documents/:docId`.
- **Dependency:** S2-T2, S2-T3.
- **Effort:** 6 hours.

#### S2-T5: Backend -- Inspection model and service

- **What:** Create the daily inspection log entity with checklist items, corrective actions, photos, and voice notes.
- **Files to create:**
  - `backend/app/models/inspection.py` -- `InspectionCreate`, `Inspection`, `ChecklistItem`, `CorrectiveAction`, `InspectionType` enum, `ChecklistResponse` enum (`pass`, `fail`, `na`, `not_inspected`).
  - `backend/app/services/inspection_service.py` -- `InspectionService` with: `create()`, `get()`, `list_inspections()`, `add_checklist_response()`, `complete()`, `get_checklist_template()`. Collection path: `companies/{cid}/projects/{pid}/inspections/{iid}`.
  - `backend/app/routers/inspections.py` -- Endpoints for CRUD + photo upload + voice note upload.
- **Files to modify:**
  - `backend/app/main.py` -- Register inspections router.
  - `backend/app/dependencies.py` -- Add `get_inspection_service()`.
- **Dependency:** S2-T1 (project entity).
- **Effort:** 10 hours.

#### S2-T6: Backend -- Checklist templates

- **What:** Pre-built checklist templates for daily safety inspections by trade and project type.
- **Files to create:**
  - `backend/app/data/checklists/` directory with JSON files: `daily_safety_general.json`, `daily_safety_electrical.json`, `daily_safety_excavation.json`, `daily_safety_scaffolding.json`. Each contains an array of `{item_id, category, question, osha_standard}`.
- **Files to modify:**
  - `backend/app/services/inspection_service.py` -- `get_checklist_template()` loads the correct JSON file based on project type and trade.
- **Dependency:** S2-T5.
- **Effort:** 4 hours.

#### S2-T7: Frontend -- Inspection pages

- **What:** Mobile-optimized inspection creation with checklist, photo capture, and voice notes.
- **Files to create:**
  - `frontend/src/components/inspections/InspectionListPage.tsx` -- List of inspections for the current project, sorted by date.
  - `frontend/src/components/inspections/InspectionCreatePage.tsx` -- Mobile-first checklist: iterate through items, tap pass/fail/NA, add notes, attach photos. GPS auto-captured. Weather auto-fetched.
  - `frontend/src/components/inspections/InspectionDetailPage.tsx` -- Read-only view of completed inspection with photos.
  - `frontend/src/components/inspections/InspectionChecklist.tsx` -- Checklist renderer component: question, pass/fail/NA buttons, notes field, photo button.
  - `frontend/src/features/inspections/useInspections.ts` -- React Query hooks.
  - `frontend/src/hooks/useCamera.ts` -- Camera capture hook using `navigator.mediaDevices.getUserMedia()`.
  - `frontend/src/hooks/useGeolocation.ts` -- GPS hook using `navigator.geolocation.getCurrentPosition()`.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes: `/projects/:projectId/inspections`, `/projects/:projectId/inspections/new`, `/projects/:projectId/inspections/:inspectionId`.
  - `frontend/src/components/projects/ProjectDetailPage.tsx` -- Add Inspections tab.
  - `frontend/src/lib/query-keys.ts` -- Add inspection query keys.
- **Dependency:** S2-T3, S2-T5.
- **Effort:** 12 hours.

#### S2-T8: Backend -- Storage service for photos and voice notes

- **What:** Implement Cloud Storage upload for photos and audio files.
- **Files to create:**
  - `backend/app/services/storage_service.py` -- `StorageService` with: `upload_photo(company_id, path_prefix, file) -> (url, thumbnail_url)`, `upload_audio(company_id, path_prefix, file) -> url`, `generate_signed_url(gcs_path, expiry_minutes) -> str`. Uses `google-cloud-storage` SDK. Bucket: `safetyforge-photos` for images, `safetyforge-audio` for voice.
- **Files to modify:**
  - `backend/app/dependencies.py` -- Add `get_storage_service()`.
  - `backend/requirements.txt` or `pyproject.toml` -- Add `google-cloud-storage`.
- **Dependency:** None.
- **Effort:** 4 hours.

**Sprint 2 Definition of Done:**
- User can create a project with all required fields.
- Documents are created within a project context.
- User can run a daily safety inspection on mobile: open checklist, mark pass/fail, take photos, add notes, complete.
- Inspection list shows all inspections for a project with date filtering.
- Project detail page shows compliance overview with document and inspection counts.

**Sprint 2 Total Estimated Effort:** 60 hours

---

### Sprint 3: Toolbox Talks + Spanish (Week 4)

**Goal:** AI-generated bilingual toolbox talks with crew sign-off. Spanish language support for all generated content and key UI strings.

#### S3-T1: Backend -- Toolbox talk model and service

- **What:** Create the toolbox talk entity with AI generation, bilingual content, and attendance tracking.
- **Files to create:**
  - `backend/app/models/toolbox_talk.py` -- `ToolboxTalkCreate`, `ToolboxTalk`, `AttendanceRecord`, `TopicCategory` enum.
  - `backend/app/services/toolbox_talk_service.py` -- `ToolboxTalkService` with: `create()`, `generate_talk()`, `record_attendance()`, `complete()`, `suggest_topic()`. Uses `GenerationService` for AI content. Collection path: `companies/{cid}/projects/{pid}/toolbox_talks/{tid}`.
  - `backend/app/routers/toolbox_talks.py` -- Endpoints per Section 2.6 of backend architecture.
- **Files to modify:**
  - `backend/app/main.py` -- Register toolbox talks router.
  - `backend/app/dependencies.py` -- Add `get_toolbox_talk_service()`.
  - `backend/app/services/generation_service.py` -- Add `generate_toolbox_talk(topic, trade, language)` method with a dedicated prompt template.
- **Dependency:** S2-T1 (project entity).
- **Effort:** 10 hours.

#### S3-T2: Backend -- Translation service

- **What:** Translate generated content to Spanish using Claude.
- **Files to create:**
  - `backend/app/services/translation_service.py` -- `TranslationService` with `translate_content(content: dict, source: str, target: str) -> dict`. Uses Claude with a construction-safety-specific translation prompt.
- **Files to modify:**
  - `backend/app/services/toolbox_talk_service.py` -- After generating English content, call `translate_content()` for Spanish. Store in `translated_content.es`.
  - `backend/app/dependencies.py` -- Add `get_translation_service()`.
- **Dependency:** S3-T1.
- **Effort:** 4 hours.

#### S3-T3: Frontend -- Toolbox talk pages

- **What:** Talk generation, bilingual delivery mode with large text, and crew sign-off.
- **Files to create:**
  - `frontend/src/components/toolbox-talks/ToolboxTalkListPage.tsx` -- List of talks for the project with status (scheduled, delivered, completed).
  - `frontend/src/components/toolbox-talks/ToolboxTalkDeliverPage.tsx` -- Full-screen delivery mode: large text, EN/ES toggle, key points displayed one at a time. "Start Sign-Off" button at the end.
  - `frontend/src/components/toolbox-talks/ToolboxTalkSignOff.tsx` -- Worker list with touch signature pad for each attendee. Workers sign on the phone screen.
  - `frontend/src/components/toolbox-talks/ToolboxTalkDetailPage.tsx` -- Read-only view of completed talk with attendance list.
  - `frontend/src/components/toolbox-talks/ToolboxTalkViewer.tsx` -- Bilingual content display component.
  - `frontend/src/components/shared/SignatureCapture.tsx` -- Touch-friendly signature pad using HTML5 Canvas.
  - `frontend/src/features/toolbox-talks/useToolboxTalks.ts` -- React Query hooks.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes for toolbox talks under `/projects/:projectId/toolbox-talks`.
  - `frontend/src/components/projects/ProjectDetailPage.tsx` -- Add Toolbox Talks tab.
  - `frontend/src/lib/query-keys.ts` -- Add toolbox talk query keys.
- **Dependency:** S3-T1.
- **Effort:** 14 hours.

#### S3-T4: Frontend -- i18n infrastructure

- **What:** Set up internationalization for the UI with English and Spanish.
- **Files to create:**
  - `frontend/src/i18n/index.ts` -- i18next setup with `react-i18next`.
  - `frontend/src/i18n/locales/en/common.json` -- English translations for all shared UI strings (buttons, labels, navigation, statuses).
  - `frontend/src/i18n/locales/es/common.json` -- Spanish translations.
  - `frontend/src/i18n/locales/en/inspections.json` -- Inspection-specific strings.
  - `frontend/src/i18n/locales/es/inspections.json` -- Spanish.
  - `frontend/src/i18n/locales/en/toolbox-talks.json` -- Toolbox talk strings.
  - `frontend/src/i18n/locales/es/toolbox-talks.json` -- Spanish.
  - `frontend/src/components/shared/LanguageToggle.tsx` -- EN/ES toggle button.
  - `frontend/src/app/providers/I18nProvider.tsx` -- Context provider for language state.
- **Files to modify:**
  - `frontend/src/main.tsx` -- Wrap app in I18nProvider.
  - `frontend/src/components/layout/Header.tsx` -- Add LanguageToggle to header.
  - `frontend/package.json` -- Add `i18next`, `react-i18next`, `i18next-browser-languagedetector`.
- **Dependency:** None.
- **Effort:** 8 hours.

#### S3-T5: Backend -- Document translation endpoint

- **What:** Add translation capability to existing safety documents.
- **Files to modify:**
  - `backend/app/routers/documents.py` -- Add `POST /companies/{cid}/projects/{pid}/documents/{did}/translate` endpoint.
  - `backend/app/services/document_service.py` -- Add `translate()` method that calls `TranslationService` and stores result in `translated_content`.
  - `backend/app/models/document.py` -- Add `translated_content: dict[str, dict] | None` field to `Document` model.
- **Dependency:** S3-T2 (translation service), S2-T2 (project-scoped documents).
- **Effort:** 3 hours.

**Sprint 3 Definition of Done:**
- User can generate a toolbox talk by topic. Content appears in both English and Spanish.
- Foreman can run the talk in full-screen delivery mode, toggle language.
- Crew members sign off with touch signatures.
- Attendance is recorded and linked to training records.
- UI can be toggled between English and Spanish for key screens.
- Existing documents can be translated to Spanish.

**Sprint 3 Total Estimated Effort:** 39 hours

---

### Sprint 4: Workers + Certifications (Week 5)

**Goal:** Worker profiles with certification tracking and expiry alerts. Workers can be assigned to projects.

#### S4-T1: Backend -- Worker model and service

- **Files to create:**
  - `backend/app/models/worker.py` -- `WorkerCreate`, `WorkerUpdate`, `Worker`, `WorkerStatus` enum, `Certification`, `CertificationCreate`, `CertificationType` enum (22 types from architecture doc), `TrainingRecord`.
  - `backend/app/services/worker_service.py` -- `WorkerService` with: `create()`, `get()`, `list_workers()`, `update()`, `delete()`, `add_certification()`, `get_expiring_certifications()`, `get_training_matrix()`, `create_training_record()`. Collection: `companies/{cid}/workers/{wid}`, subcollection: `certifications/{certid}`, `training_records/{rid}`.
  - `backend/app/routers/workers.py` -- All endpoints from Section 2.9 of backend architecture.
- **Files to modify:**
  - `backend/app/main.py` -- Register workers router.
  - `backend/app/dependencies.py` -- Add `get_worker_service()`.
- **Dependency:** S0-T8 (DI pattern).
- **Effort:** 10 hours.

#### S4-T2: Backend -- Certification expiry alert job

- **What:** Cloud Scheduler job that runs daily, checks all certifications expiring within 30/14/7/1 days, and creates notification records.
- **Files to create:**
  - `backend/app/services/notification_service.py` -- `NotificationService` with `create_alert()` and `get_alerts()`. Initially stores alerts in Firestore `companies/{cid}/notifications/{nid}`. Email notifications deferred to Sprint 5.
  - `backend/app/jobs/cert_expiry_check.py` -- Callable function that queries all certifications with `expiry_date` in the alert windows. Creates notification records.
  - `backend/app/routers/jobs.py` -- Internal endpoint `POST /jobs/cert-expiry-check` called by Cloud Scheduler (authenticated via service account).
- **Files to modify:**
  - `backend/app/main.py` -- Register jobs router.
- **Dependency:** S4-T1.
- **Effort:** 6 hours.

#### S4-T3: Frontend -- Worker management pages

- **Files to create:**
  - `frontend/src/components/workers/WorkerListPage.tsx` -- Searchable list with trade filter, certification status badges.
  - `frontend/src/components/workers/WorkerCreatePage.tsx` -- Form: first name, last name, trade, phone, preferred language, emergency contact.
  - `frontend/src/components/workers/WorkerDetailPage.tsx` -- Profile with certification cards, training history timeline, project assignments.
  - `frontend/src/components/workers/CertificationCard.tsx` -- Single cert display: name, expiry date, status badge (green=current, yellow=expiring, red=expired), proof document link.
  - `frontend/src/features/workers/useWorkers.ts` -- React Query hooks for all worker/cert endpoints.
  - `frontend/src/features/workers/useCertifications.ts` -- Hooks for certification CRUD.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes: `/workers`, `/workers/new`, `/workers/:workerId`.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add "Workers" nav item under "People" section.
  - `frontend/src/lib/query-keys.ts` -- Add worker and certification query keys.
- **Dependency:** S4-T1.
- **Effort:** 10 hours.

#### S4-T4: Frontend -- Training matrix

- **Files to create:**
  - `frontend/src/components/workers/TrainingMatrix.tsx` -- Grid view: rows = workers, columns = certification types. Cells show green/yellow/red/empty. Filterable by trade. Exportable to PDF.
  - `frontend/src/components/training/TrainingDashboard.tsx` -- Summary view: total certifications, expiring soon count, training hours this month.
  - `frontend/src/components/training/ExpirationAlerts.tsx` -- Alert list component showing upcoming expirations.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes: `/training`, `/training/matrix`.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add "Training" nav item.
- **Dependency:** S4-T3.
- **Effort:** 8 hours.

#### S4-T5: Link workers to project and inspections

- **What:** Workers can be assigned to projects. Toolbox talk attendance selects from assigned workers.
- **Files to modify:**
  - `frontend/src/components/projects/ProjectDetailPage.tsx` -- Add "Crew" tab showing assigned workers with add/remove.
  - `backend/app/services/project_service.py` -- Add `assign_workers()` and `remove_workers()` methods.
  - `frontend/src/components/toolbox-talks/ToolboxTalkSignOff.tsx` -- Load assigned workers for the project as the default attendee list.
- **Dependency:** S4-T1, S2-T1, S3-T3.
- **Effort:** 4 hours.

**Sprint 4 Definition of Done:**
- User can add workers with trade and contact info.
- User can add certifications with expiry dates and proof documents.
- Training matrix shows all workers x all cert types.
- Expiring certifications appear as alerts on the dashboard.
- Workers can be assigned to projects.
- Toolbox talk sign-off pre-populates from assigned workers.

**Sprint 4 Total Estimated Effort:** 38 hours

---

### Sprint 5: Dashboard + OSHA 300 (Week 6)

**Goal:** Multi-project compliance dashboard showing real data. OSHA 300 Log management for annual recordkeeping.

#### S5-T1: Backend -- Dashboard aggregation endpoint

- **What:** The `GET /companies/{cid}/dashboard` endpoint that pulls compliance scores, recent activity, and alerts from all projects.
- **Files to modify:**
  - `backend/app/services/company_service.py` -- Implement `get_dashboard()` that queries: all active projects (compliance scores), recent inspections (last 7 days), open corrective actions, expiring certifications, recent hazard reports.
  - `backend/app/routers/companies.py` -- Wire up `GET /companies/{cid}/dashboard` endpoint.
- **Dependency:** S2-T1, S2-T5, S4-T1 (all entities must exist).
- **Effort:** 6 hours.

#### S5-T2: Frontend -- Refactor DashboardPage for multi-project view

- **Files to modify:**
  - `frontend/src/components/dashboard/DashboardPage.tsx` -- Complete rewrite. Show: project cards with compliance status (green/yellow/red), quick actions (New Inspection, Toolbox Talk, Hazard Report), upcoming deadlines, recent activity feed.
- **Files to create:**
  - `frontend/src/components/dashboard/ComplianceOverview.tsx` -- Grid of project cards with compliance score rings and status indicators.
  - `frontend/src/components/dashboard/QuickActions.tsx` -- Action cards that link to daily tasks for the selected project.
  - `frontend/src/components/dashboard/UpcomingDeadlines.tsx` -- List of cert expirations, inspection due dates, submission deadlines.
  - `frontend/src/components/dashboard/RecentActivity.tsx` -- Activity feed: inspections, documents, hazard reports, toolbox talks.
- **Dependency:** S5-T1.
- **Effort:** 10 hours.

#### S5-T3: Backend -- Incident management (basic)

- **What:** Basic incident reporting needed for OSHA 300 Log. Full investigation workflow is Sprint 9.
- **Files to create:**
  - `backend/app/models/incident.py` -- `IncidentCreate`, `Incident`, `IncidentType` enum, `IncidentSeverity` enum.
  - `backend/app/services/incident_service.py` -- `IncidentService` with: `create()`, `get()`, `list_incidents()`, `get_osha_300_log()`, `generate_osha_300a_summary()`. The OSHA 300 log is a computed view from all recordable incidents in a calendar year.
  - `backend/app/routers/incidents.py` -- CRUD endpoints + `GET /companies/{cid}/osha-300-log?year=2026` + `GET /companies/{cid}/osha-300a-summary?year=2026`.
- **Files to modify:**
  - `backend/app/main.py` -- Register incidents router.
  - `backend/app/dependencies.py` -- Add `get_incident_service()`.
- **Dependency:** S2-T1.
- **Effort:** 10 hours.

#### S5-T4: Frontend -- OSHA 300 Log page

- **Files to create:**
  - `frontend/src/components/analytics/Osha300Page.tsx` -- OSHA 300 Log viewer: table format matching the actual OSHA 300 form layout. Year selector. Auto-calculated incidence rates. "Generate 300A Summary" button. "Export PDF" button.
  - `frontend/src/features/analytics/useAnalytics.ts` -- React Query hooks for analytics endpoints.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add route: `/analytics/osha-300`.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add "Analytics" section with "OSHA 300 Log" item.
- **Dependency:** S5-T3.
- **Effort:** 8 hours.

#### S5-T5: Backend -- Analytics endpoints (basic)

- **Files to create:**
  - `backend/app/services/analytics_service.py` -- `AnalyticsService` with: `get_compliance_trend()`, `get_incident_rates()`, `get_inspection_activity()`. Queries Firestore with date range filters, returns time-series data.
  - `backend/app/routers/analytics.py` -- Endpoints from Section 2.13 of backend architecture.
- **Files to modify:**
  - `backend/app/main.py` -- Register analytics router.
- **Dependency:** S2-T5, S5-T3.
- **Effort:** 6 hours.

#### S5-T6: Frontend -- Project picker and context

- **What:** Add a project picker dropdown to the header so users can switch active projects without going back to the project list.
- **Files to create:**
  - `frontend/src/components/layout/ProjectPicker.tsx` -- Dropdown showing active projects with compliance status dots. Selecting a project sets the `ProjectContext`.
  - `frontend/src/app/providers/ProjectProvider.tsx` -- React Context that holds the current project ID and data. Persists selection to localStorage.
- **Files to modify:**
  - `frontend/src/components/layout/Header.tsx` -- Add ProjectPicker component.
  - `frontend/src/main.tsx` -- Wrap app in ProjectProvider.
- **Dependency:** S2-T3.
- **Effort:** 4 hours.

**Sprint 5 Definition of Done:**
- Dashboard shows real compliance data across all projects.
- Each project shows green/yellow/red compliance status.
- Expiring certifications and overdue inspections surface as alerts.
- Incidents can be reported with basic fields.
- OSHA 300 Log auto-generates from recorded incidents.
- OSHA 300A annual summary can be generated and exported.
- User can switch active project from the header.

**Sprint 5 Total Estimated Effort:** 44 hours

---

**--- END OF PHASE 1 ---**

Phase 1 exit criteria from product strategy: A contractor can sign up, configure their company and projects, generate all required written programs, run daily toolbox talks and inspections from mobile, and have a dashboard showing compliance status. Worth $200-400/month.

---

### Sprint 6: Mock OSHA Inspection (Weeks 7-8)

**Goal:** The killer feature. AI audits all company documents, inspections, training records, and certifications against applicable OSHA standards and returns findings in citation format with a readiness score.

#### S6-T1: Backend -- Mock inspection service

- **Files to create:**
  - `backend/app/models/mock_inspection.py` -- `MockInspection`, `MockInspectionCreate`, `Finding`, `CategoryAssessment`, `MockInspectionStatus` enum.
  - `backend/app/services/mock_inspection_service.py` -- `MockInspectionService` that:
    1. Gathers all data: documents, inspections, training records, certifications, equipment, hazard reports, incidents for the target project.
    2. Builds a comprehensive context prompt for Claude.
    3. Sends to Claude with a system prompt that acts as an OSHA compliance officer.
    4. Parses findings into the structured format (standard, observed condition, requirement, recommended action, estimated penalty).
    5. Calculates overall score (0-100) and per-category scores.
    6. Stores results in `companies/{cid}/mock_inspections/{mid}`.
  - `backend/app/routers/mock_inspections.py` -- `POST /companies/{cid}/mock-inspections` (returns 202, async), `GET .../status` (poll), `GET .../{mid}` (results).
- **Files to modify:**
  - `backend/app/main.py` -- Register mock inspections router.
  - `backend/app/dependencies.py` -- Add `get_mock_inspection_service()` with all required service dependencies.
  - `backend/app/services/generation_service.py` -- Add `generate_mock_inspection()` method with the OSHA auditor prompt.
- **Dependency:** All Sprint 2-5 entities.
- **Effort:** 20 hours.

#### S6-T2: Backend -- Regulatory standards collection

- **What:** Seed the `regulatory_standards` collection with the most frequently cited OSHA construction standards.
- **Files to create:**
  - `backend/app/data/osha_standards/` directory with JSON files for the top 25 cited standards (1926.501, 1926.451, 1926.1053, 1926.503, 1910.147, etc.). Each file contains the structured standard data from Section 1.14 of backend architecture.
  - `backend/app/scripts/seed_standards.py` -- Script to load JSON files into Firestore `regulatory_standards` collection.
- **Dependency:** None.
- **Effort:** 8 hours.

#### S6-T3: Frontend -- Mock inspection pages

- **Files to create:**
  - `frontend/src/components/mock-inspection/MockInspectionPage.tsx` -- Run inspection form: select project (or company-wide), select categories, "Run Inspection" button. Shows progress during generation (estimated 2-4 minutes).
  - `frontend/src/components/mock-inspection/MockInspectionResults.tsx` -- Results page: overall score ring (0-100), grade letter, per-category breakdown with scores, finding list in OSHA citation format, comparison with previous score.
  - `frontend/src/components/mock-inspection/FindingCard.tsx` -- Individual finding: OSHA standard reference, observed condition, requirement text, recommended action, estimated penalty, severity badge.
  - `frontend/src/components/mock-inspection/MockInspectionHistory.tsx` -- Past inspections with score trend chart.
  - `frontend/src/features/mock-inspection/useMockInspection.ts` -- React Query hooks with polling for async generation.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes: `/mock-inspection`, `/mock-inspection/new`, `/mock-inspection/:inspectionId`.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add "Mock OSHA Inspection" under Compliance section.
- **Dependency:** S6-T1.
- **Effort:** 14 hours.

#### S6-T4: Backend -- Mock inspection PDF report

- **What:** Generate a professional PDF report from mock inspection results.
- **Files to modify:**
  - `backend/app/services/pdf_service.py` -- Add `generate_mock_inspection_pdf()` that creates an OSHA-style inspection report with cover page, score summary, findings list with citations, and recommendations.
  - `backend/app/routers/mock_inspections.py` -- Add `POST /companies/{cid}/mock-inspections/{mid}/pdf`.
- **Dependency:** S6-T1.
- **Effort:** 6 hours.

**Sprint 6 Definition of Done:**
- User can trigger a mock OSHA inspection for a project.
- System gathers all project data (documents, inspections, certifications, etc.) and runs AI analysis.
- Results show overall readiness score, per-category scores, and individual findings in OSHA citation format.
- Findings include specific standard references, recommended actions, and estimated penalties.
- Score history shows improvement trend.
- PDF report can be generated and downloaded.

**Sprint 6 Total Estimated Effort:** 48 hours (2 weeks at reduced pace, or 1 intense week)

---

### Sprint 7: Photo Hazard Assessment (Weeks 8-9)

**Goal:** Take a jobsite photo, get AI hazard analysis with OSHA references and recommended corrective actions.

#### S7-T1: Backend -- Photo analysis service

- **Files to create:**
  - `backend/app/services/photo_analysis_service.py` -- `PhotoAnalysisService` with `analyze_hazard(image_bytes, context)` that sends the image to Claude Vision with a construction-safety-specific system prompt. Returns: `{hazard_identified, osha_standards: [{standard, description}], risk_level, recommended_actions: [], confidence_score}`.
- **Dependency:** S2-T8 (storage service).
- **Effort:** 6 hours.

#### S7-T2: Backend -- Hazard report model and service

- **Files to create:**
  - `backend/app/models/hazard_report.py` -- `HazardReportCreate`, `HazardReport`, `AIAnalysis`, `ReportType` enum, `Severity` enum, `HazardStatus` enum.
  - `backend/app/services/hazard_report_service.py` -- `HazardReportService` with: `create()`, `add_photo()`, `add_voice_note()`, `analyze_photos()`, `resolve()`. Collection: `companies/{cid}/projects/{pid}/hazard_reports/{rid}`.
  - `backend/app/routers/hazard_reports.py` -- All endpoints from Section 2.7 of backend architecture.
- **Files to modify:**
  - `backend/app/main.py` -- Register hazard reports router.
  - `backend/app/dependencies.py` -- Add services.
- **Dependency:** S7-T1, S2-T8.
- **Effort:** 8 hours.

#### S7-T3: Frontend -- Hazard report pages

- **Files to create:**
  - `frontend/src/components/hazards/HazardListPage.tsx` -- List with severity and status filters.
  - `frontend/src/components/hazards/HazardReportPage.tsx` -- Mobile-first report creation: photo capture (primary), voice note, text description, location auto-detection. AI analysis appears after photo upload.
  - `frontend/src/components/hazards/HazardDetailPage.tsx` -- Full report view with AI analysis, corrective action status, resolution verification photo.
  - `frontend/src/components/hazards/HazardAnalysisCard.tsx` -- AI analysis display: identified hazard, OSHA references, risk level, recommended actions.
  - `frontend/src/components/shared/PhotoCapture.tsx` -- Camera capture component with preview, retake, and upload.
  - `frontend/src/features/hazards/useHazards.ts` -- React Query hooks.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add hazard routes under project scope.
  - `frontend/src/components/projects/ProjectDetailPage.tsx` -- Add Hazards tab.
- **Dependency:** S7-T2.
- **Effort:** 12 hours.

**Sprint 7 Definition of Done:**
- Foreman can take a photo on the jobsite and get immediate AI hazard analysis.
- Analysis includes specific OSHA standard references and recommended actions.
- Hazard reports track from creation through corrective action to resolution.
- Voice notes can be attached to hazard reports.
- Resolution requires a verification photo.

**Sprint 7 Total Estimated Effort:** 26 hours

---

### Sprint 8: Morning Safety Brief (Weeks 9-10)

**Goal:** Daily proactive risk scoring per project that surfaces the 3-5 things a foreman needs to know before the crew arrives.

#### S8-T1: Backend -- Weather service integration

- **Files to create:**
  - `backend/app/services/weather_service.py` -- `WeatherService` with: `get_forecast(lat, lng)`, `get_current(lat, lng)`, `get_alerts(lat, lng)`. Uses OpenWeatherMap or WeatherAPI free tier. Returns temperature, conditions, wind, precipitation, and safety-relevant alerts.
- **Dependency:** None.
- **Effort:** 4 hours.

#### S8-T2: Backend -- Risk scoring service

- **Files to create:**
  - `backend/app/services/risk_scoring_service.py` -- `RiskScoringService` with `calculate_project_risk(project, weather, certifications, recent_incidents, open_hazards) -> RiskScore`. Algorithm weights: weather (20%), certification gaps (25%), recent incidents (20%), open hazards (20%), inspection gaps (15%). Returns score 0-10 with risk level and contributing factors.
- **Dependency:** S4-T1, S5-T3, S7-T2.
- **Effort:** 6 hours.

#### S8-T3: Backend -- Morning brief service

- **Files to create:**
  - `backend/app/services/morning_brief_service.py` -- `MorningBriefService` that assembles: risk score, weather data, certification alerts, recommended toolbox talk topic, open corrective actions, yesterday's activity summary. Returns the structured brief per Section 2.3 of backend architecture.
- **Files to modify:**
  - `backend/app/routers/projects.py` -- Add `POST /companies/{cid}/projects/{pid}/morning-brief`.
- **Dependency:** S8-T1, S8-T2, S3-T1.
- **Effort:** 8 hours.

#### S8-T4: Frontend -- Morning brief page

- **Files to create:**
  - `frontend/src/components/morning-brief/MorningBriefPage.tsx` -- Full-screen brief view: risk score ring at top, weather card, risk factors list with severity indicators, cert expiry alerts, recommended toolbox talk with one-tap generation, open corrective actions.
  - `frontend/src/components/morning-brief/RiskScoreDisplay.tsx` -- Animated score ring (0-10) with color gradient (green to red).
  - `frontend/src/components/morning-brief/BriefActionItems.tsx` -- List of actionable items with tap-to-action (generate talk, view cert, etc.).
  - `frontend/src/features/morning-brief/useMorningBrief.ts` -- React Query hooks.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add route: `/projects/:projectId/morning-brief`.
  - `frontend/src/components/projects/ProjectDetailPage.tsx` -- Add "Morning Brief" as the first tab.
- **Dependency:** S8-T3.
- **Effort:** 8 hours.

**Sprint 8 Definition of Done:**
- At 5:45 AM (or any time), a foreman opens the Morning Brief for their project.
- Brief shows risk score, weather, cert alerts, and recommended toolbox talk.
- One-tap actions: generate the recommended talk, view expiring cert, review open corrective actions.
- Risk score updates based on real project data (weather, certs, incidents, hazards).

**Sprint 8 Total Estimated Effort:** 26 hours

---

### Sprint 9: Voice Input + Incidents (Weeks 10-11)

**Goal:** Voice-dictated field reports for loud/gloves-on environments. Full incident investigation workflow.

#### S9-T1: Backend -- Voice transcription service

- **Files to create:**
  - `backend/app/services/voice_service.py` -- `VoiceService` with: `transcribe(audio_bytes, source_language) -> Transcript` using OpenAI Whisper API or Google Speech-to-Text. `structure_report(transcript, report_type) -> dict` that uses Claude to extract structured fields from the transcript.
- **Dependency:** S2-T8 (storage service).
- **Effort:** 6 hours.

#### S9-T2: Frontend -- Voice input component

- **Files to create:**
  - `frontend/src/components/shared/VoiceInput.tsx` -- Record button component using Web MediaRecorder API. Shows recording waveform, stop button, playback preview. Uploads to backend and displays transcript.
  - `frontend/src/hooks/useVoiceInput.ts` -- Hook wrapping MediaRecorder: `startRecording()`, `stopRecording()`, `audioBlob`, `isRecording`, `duration`.
- **Files to modify:**
  - `frontend/src/components/hazards/HazardReportPage.tsx` -- Add VoiceInput as an alternative to text description.
  - `frontend/src/components/inspections/InspectionCreatePage.tsx` -- Add VoiceInput for inspection notes.
- **Dependency:** S9-T1.
- **Effort:** 8 hours.

#### S9-T3: Backend -- Full incident investigation workflow

- **Files to modify:**
  - `backend/app/services/incident_service.py` -- Add: `start_investigation()`, `update_investigation()`, `generate_osha_forms()`. Investigation includes 5-Why and fishbone root cause analysis. OSHA forms (301, 300 entry) are AI-generated from incident data.
  - `backend/app/models/incident.py` -- Add `Investigation`, `CorrectiveAction`, `OshaForms` models.
  - `backend/app/routers/incidents.py` -- Add investigation endpoints, voice report upload, OSHA form generation.
- **Dependency:** S5-T3 (basic incidents), S9-T1.
- **Effort:** 10 hours.

#### S9-T4: Frontend -- Incident management pages

- **Files to create:**
  - `frontend/src/components/incidents/IncidentListPage.tsx` -- List with severity and status filters.
  - `frontend/src/components/incidents/IncidentReportPage.tsx` -- Voice-first incident capture: large record button, photo attach, auto-transcription fills form fields.
  - `frontend/src/components/incidents/IncidentDetailPage.tsx` -- Full incident view with timeline.
  - `frontend/src/components/incidents/IncidentTimeline.tsx` -- Chronological timeline: reported, investigation started, findings, corrective actions, closed.
  - `frontend/src/components/incidents/RootCauseAnalysis.tsx` -- Guided 5-Why flow: each "Why?" is a step, AI suggests causes.
  - `frontend/src/features/incidents/useIncidents.ts` -- React Query hooks.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add incident routes.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add "Incidents" nav item.
- **Dependency:** S9-T3.
- **Effort:** 14 hours.

**Sprint 9 Definition of Done:**
- Voice input works on hazard reports, inspections, and incident reports.
- Transcription supports English and Spanish.
- Full incident investigation flow: report, investigate (5-Why), corrective actions, closure.
- OSHA 301 form auto-generates from incident data.
- Incident appears in OSHA 300 Log automatically.

**Sprint 9 Total Estimated Effort:** 38 hours

---

### Sprint 10: Analytics + EMR (Weeks 11-12)

**Goal:** Safety analytics dashboard with compliance trends, incident rates, and EMR impact modeling.

#### S10-T1: Backend -- EMR projection service

- **Files to create:**
  - `backend/app/services/emr_service.py` -- `EmrService` with `calculate_emr_projection(company_id, year) -> EmrProjection`. Uses NCCI EMR formula: (actual losses / expected losses) x experience modification. Inputs: company's incident data (DART rate, TRIR), industry averages by NAICS code, payroll estimate. Returns current EMR, projected EMR, and estimated premium impact in dollars.
- **Dependency:** S5-T3 (incidents).
- **Effort:** 8 hours.

#### S10-T2: Frontend -- Analytics dashboard

- **Files to create:**
  - `frontend/src/components/analytics/AnalyticsDashboard.tsx` -- Charts: compliance score trend (line), inspection completion rate (bar), incident frequency (line), hazard reports by category (pie), training coverage (gauge).
  - `frontend/src/components/analytics/EmrModelingPage.tsx` -- EMR calculator: current EMR input, projected EMR based on current safety data, dollar impact on insurance premium, comparison to industry average.
  - `frontend/src/components/analytics/TrendCharts.tsx` -- Reusable chart components using Recharts or Chart.js.
  - `frontend/src/components/analytics/ComplianceScoreTrend.tsx` -- Per-project compliance score over time.
- **Files to modify:**
  - `frontend/src/App.tsx` -- Add routes: `/analytics`, `/analytics/emr`.
  - `frontend/src/components/layout/Sidebar.tsx` -- Add Analytics section items.
  - `frontend/package.json` -- Add `recharts` or `chart.js` + `react-chartjs-2`.
- **Dependency:** S10-T1, S5-T5.
- **Effort:** 12 hours.

#### S10-T3: Backend -- Compliance scoring refinement

- **What:** The compliance score is currently a placeholder. Implement the actual scoring algorithm.
- **Files to modify:**
  - `backend/app/services/project_service.py` -- `update_compliance_score()` calculates score from: documents exist for required types (30%), inspections current (25%), certifications current (20%), toolbox talks on schedule (15%), open corrective actions (10%). Deductions for each gap.
- **Dependency:** All Phase 1 entities.
- **Effort:** 4 hours.

#### S10-T4: Tests -- Comprehensive test suite

- **What:** Before Phase 2 launch, add comprehensive tests for all critical paths.
- **Files to create:**
  - `backend/tests/test_project_service.py` -- CRUD, compliance scoring, worker assignment.
  - `backend/tests/test_inspection_service.py` -- Create, complete, checklist template loading.
  - `backend/tests/test_toolbox_talk_service.py` -- Create, attendance recording, training record creation.
  - `backend/tests/test_worker_service.py` -- CRUD, certification management, expiry queries.
  - `backend/tests/test_incident_service.py` -- CRUD, OSHA 300 log generation, investigation workflow.
  - `backend/tests/test_mock_inspection_service.py` -- Data gathering, scoring, finding generation.
  - `frontend/src/__tests__/DocumentCreatePage.test.tsx` -- Component test for document creation flow.
  - `frontend/src/__tests__/InspectionChecklist.test.tsx` -- Component test for checklist interaction.
- **Dependency:** All sprints.
- **Effort:** 12 hours.

**Sprint 10 Definition of Done:**
- Analytics dashboard shows real trends from all project data.
- EMR modeling shows contractors their projected insurance impact.
- Compliance scoring uses the real algorithm based on all entity data.
- Comprehensive test suite passes for all services.
- All Phase 2 features are functional end-to-end.

**Sprint 10 Total Estimated Effort:** 36 hours

---

**--- END OF PHASE 2 ---**

---

## ARCHITECTURE DECISIONS LOG

### ADR-001: Firestore over Postgres

**Context:** The data model is hierarchical (companies -> projects -> documents/inspections) and document-oriented (each entity is a self-contained JSON blob with varying schemas per document type).

**Decision:** Firestore.

**Rationale:** (1) Natural fit for hierarchical, document-oriented data. (2) Zero-ops -- no connection pooling, no migrations, no vacuum. (3) Built-in realtime subscriptions for future live dashboards. (4) Firebase Auth integration is seamless. (5) Offline persistence for mobile fieldwork is built in. (6) Cost-effective at our scale (reads dominate writes).

**Trade-off:** No JOINs means the mock inspection service must make many reads to assemble its context. Mitigated by Firestore's fast reads and the fact that mock inspections are infrequent (monthly) and tolerate 2-4 minute latency.

### ADR-002: Per-project pricing, not per-user

**Context:** Construction crews have 10-50+ field workers who need to use the app (inspections, toolbox talks). Per-user pricing at even $10/user/month would cost $500/month for a 50-person crew, killing adoption.

**Decision:** Per-project pricing with unlimited users.

**Rationale:** (1) Eliminates adoption friction -- every foreman and laborer can use the app. (2) Aligns with how contractors think about costs (per job). (3) Creates natural upsell as companies take on more projects. (4) Competitive advantage vs SafetyCulture/Procore which charge per-user.

### ADR-003: Cloud Run over App Engine

**Context:** Need a Python backend (FastAPI) with auto-scaling and minimal ops.

**Decision:** Cloud Run.

**Rationale:** (1) Container-based, so we can use WeasyPrint for PDF generation (requires system packages). (2) Scales to zero in dev/staging. (3) Pay per request, not per instance. (4) Concurrency of 80 per instance handles our workload. (5) 300s timeout accommodates long AI generation calls. App Engine Standard has a 60s timeout; App Engine Flexible is more expensive.

### ADR-004: No Redis initially

**Context:** Caching could speed up dashboard loads and reduce Firestore reads.

**Decision:** No Redis until proven needed.

**Rationale:** (1) Firestore reads are fast (<50ms) and cheap at our scale (first 50K reads/day free). (2) Redis adds operational complexity and $25-100/month on Memorystore. (3) React Query provides client-side caching with configurable stale times. (4) If caching becomes necessary, Cloud Run supports Memorystore Redis; we can add it without architecture changes.

### ADR-005: React Query over Redux

**Context:** Need state management for API data, loading states, and error handling.

**Decision:** TanStack React Query with React Context for auth/project/i18n state.

**Rationale:** (1) 95% of our state is server state (CRUD data); React Query is purpose-built for this. (2) Automatic caching, background refetching, and stale-while-revalidate. (3) Optimistic updates for offline-first field operations. (4) Redux would add boilerplate with no benefit for our use case. (5) React Context handles the remaining 5% (auth, current project, language).

### ADR-006: Offline-first matters

**Context:** Construction sites often have poor or no connectivity. If a foreman cannot submit an inspection because of cell coverage, they will stop using the app.

**Decision:** Offline-first architecture with IndexedDB queue and background sync.

**Rationale:** (1) Field operations (inspections, toolbox talks, hazard reports) must work without connectivity. (2) IndexedDB stores queued mutations; service worker syncs when online. (3) Optimistic UI shows the mutation immediately. (4) GPS coordinates and timestamps are captured at creation time, not sync time. (5) Deferred to Sprint 11+ for full implementation, but the architecture supports it from Sprint 0.

### ADR-007: Spanish is Phase 1, not Phase 2

**Context:** 40-60% of construction workers in the US are Spanish-speaking. Bilingual toolbox talks are not a nice-to-have.

**Decision:** Spanish language support is a Phase 1 requirement (Sprint 3).

**Rationale:** (1) Toolbox talks delivered only in English exclude half the crew. (2) OSHA requires training in a language workers understand. (3) Competitive differentiator -- most construction safety tools are English-only. (4) Using Claude for translation means marginal cost per translation is negligible. (5) Building i18n infrastructure early means all subsequent features are bilingual from day one.

---

## RISK REGISTER

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | **AI generates incorrect OSHA references in mock inspection** | Critical -- contractor trusts result and misses real violation | Medium | Every finding includes the specific CFR section number. Build a validation layer that checks cited standards exist in the `regulatory_standards` collection. Add confidence scores to each finding. Mandatory disclaimer on all AI-generated content. |
| 2 | **Claude API latency makes document generation feel broken** | High -- user thinks app is hung, abandons | Medium | Implement 202 Accepted pattern with polling. Show progress indicator with estimated time. Cache common document templates to reduce generation time. Set a 120-second timeout with graceful failure message. |
| 3 | **Firestore read costs spike with mock inspection (reads all entities)** | Medium -- unexpected billing | Low | Mock inspections read from 5-7 collections per project. At 100 monthly inspections, that is ~50K reads/month -- well within free tier. Monitor with Cloud Monitoring alerts. Add read caching in the mock inspection service if costs exceed $50/month. |
| 4 | **Frontend-backend contract drifts again after Sprint 0 fix** | High -- regression to broken state | Medium | Add integration tests (Sprint 0-T11) that call real backend endpoints. Run in CI on every PR. Add TypeScript codegen from OpenAPI spec (the backend FastAPI auto-generates this). |
| 5 | **Photo uploads fail on poor connectivity** | High -- core field feature broken | High | Implement chunked uploads with resume capability. Queue failed uploads in IndexedDB. Auto-retry on connectivity restoration. Show clear upload status indicator. |
| 6 | **WeasyPrint PDF generation fails or produces poor output** | Medium -- PDF export is a selling point | Low | Test PDF generation for all document types in CI. Use HTML templates with consistent styling. If WeasyPrint proves unreliable, fall back to Puppeteer/Playwright for HTML-to-PDF rendering. |
| 7 | **Lemon Squeezy webhook delivery fails, subscription state gets stale** | High -- user pays but does not get access | Low | Implement webhook retry handling. Add a daily reconciliation job that checks Lemon Squeezy API for any missed events. Log all webhook events for debugging. |
| 8 | **i18n translation quality is inconsistent** | Medium -- Spanish-speaking users get confusing content | Medium | Use construction-safety-specific translation prompts with glossary of industry terms. Have native Spanish speakers review initial translations. Build a translation review pipeline for generated content. |
| 9 | **Cold start latency on Cloud Run after idle period** | Medium -- first request takes 5-10 seconds | Medium | Set `min-instances=1` in production. Use lightweight health check that warms up Firebase and Firestore connections. Monitor cold start frequency in Cloud Monitoring. |
| 10 | **Single-developer velocity cannot meet 12-week timeline** | High -- plan assumes full-time velocity | High | Prioritize ruthlessly: Sprint 0-2 are non-negotiable. Sprints 3-5 can be parallelized. Sprints 6-10 can slip 2-3 weeks without business impact. Use Claude Code for implementation acceleration. Identify one contracted frontend developer for Sprint 3-4 if needed. |

---

## DEFINITION OF DONE (Global)

Every task across all sprints must meet these criteria before it is considered done:

### Code Quality
- All new functions have type hints (Python type annotations, TypeScript types).
- All new public functions have docstrings (Google style for Python, JSDoc for TypeScript).
- No `any` types in TypeScript (use `unknown` if truly unknown).
- No `# type: ignore` without an inline justification comment.
- Imports follow the project convention: stdlib, third-party, local (separated by blank lines).

### Testing
- Backend: At least one happy-path test per new service method, running against Firestore emulator.
- Frontend: Component tests for any new page or complex component.
- No mocks for internal services. Only mock external dependencies (Claude API, weather API, Lemon Squeezy).
- Tests pass in CI before merge.

### API Contract
- Backend endpoint has request/response models defined in Pydantic.
- Frontend API call has TypeScript types matching the backend models.
- Any endpoint change updates the OpenAPI spec (auto-generated by FastAPI).

### Security
- All endpoints (except health, signup, webhook) require Bearer token authentication.
- All data access verifies company ownership via `_verify_company_access()`.
- No secrets in code, environment variables, or committed files.
- Input validation on all user-provided data (Pydantic on backend, form validation on frontend).

### UI
- New pages have loading, error, and empty states.
- New pages work on mobile viewport (375px width minimum).
- New pages are accessible: form labels, ARIA attributes on interactive elements, keyboard navigation.
- Colors and typography use design tokens, not hardcoded values.

### Documentation
- CHANGELOG updated for each sprint completion.
- Architecture decisions documented if the implementation deviates from this plan.
- Handoff document created after each sprint with: what was built, what is next, known issues, test status.

---

*This document is the execution authority for SafetyForge development. Every sprint, every task, every file path traces back to the architecture documents and product strategy. If a task is not in this plan, it does not get built until the plan is updated.*
