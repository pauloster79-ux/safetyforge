# Phase 4 Handoff: Fresh Frontend Shell

## What was just completed (Phase 1)

The backend has been migrated to the Kerf Ontology v3.0. All services updated, 12 new services created, MCP tools updated. The frontend was NOT touched in Phase 1 (except pre-existing changes from prior work).

## What this phase builds

A new frontend shell purpose-built for conversational-first interaction. Chat is the primary pane, not a sidebar overlay. Existing pages become canvas detail views.

## Current frontend architecture (read these files first)

### Layout & routing
- `frontend/src/App.tsx` — router with ProtectedRoute/PublicRoute guards, AppLayout wrapper
- `frontend/src/components/layout/AppLayout.tsx` — current shell: sidebar (240px) + header + `<Outlet />` + footer. ChatPanel mounted at layout level as a fixed overlay.
- `frontend/src/components/layout/Sidebar.tsx` — full nav sidebar with section groups
- `frontend/src/components/layout/Header.tsx` — top bar with company name, locale toggle, user menu

### Chat infrastructure (already production quality — reuse all of this)
- `frontend/src/hooks/useChat.ts` — streaming state machine. Manages messages[], isStreaming, mode (general/inspection), sessionId. Methods: sendMessage, startInspection, cancel, clear.
- `frontend/src/lib/chat-stream.ts` — async generator parsing SSE from `/me/chat`
- `frontend/src/lib/demo-chat.ts` — full demo mode simulation (no backend required)
- `frontend/src/components/chat/ChatPanel.tsx` — fixed right overlay drawer (400px). Contains MessageBubble rendering, input bar with send button. Has a floating toggle FAB.

### Voice infrastructure (reuse, don't rebuild)
- `frontend/src/hooks/useVoiceConversation.ts` — full duplex voice (STT + TTS)
- `frontend/src/hooks/useVoiceRecorder.ts` — raw mic recording
- `frontend/src/hooks/useVoiceTranscription.ts` — STT only
- `frontend/src/components/voice-inspection/VoiceInspectionPage.tsx` — full-screen conversational experience with visual orb, live transcript, streaming TTS. This is the TEMPLATE for the conversational-first pattern.

### UI primitives (reuse all)
- `frontend/src/components/ui/` — button, input, textarea, label, card, badge, avatar, alert, dialog, dropdown-menu, select, separator, sheet, sonner, table, tabs
- Built on `@base-ui/react` primitives + Tailwind CSS v4
- Design tokens in `frontend/src/index.css`: primary yellow `#F5B800`, IBM Plex Sans/Mono fonts, tight 3px radius

### Data hooks (reuse all)
- `frontend/src/hooks/` — useProjects, useWorkers, useInspections, useIncidents, useDocuments, useToolboxTalks, useMorningBrief, useOshaLog, useDailyLogs, useHazardReports, useEquipment, useEnvironmental, useMembers, usePrequalification, useGcPortal, useAnalytics

### Auth (reuse)
- `frontend/src/hooks/useAuth.ts`, `useClerkAuth.ts`
- `frontend/src/lib/clerk.ts`
- `frontend/src/components/auth/ProtectedRoute.tsx`, `PublicRoute.tsx`

## Target layout

```
Desktop (>1024px):
┌────────┬───────────────────┬────────────────────────┐
│        │                   │                        │
│  Icon  │    Chat Pane      │    Canvas Pane         │
│  Rail  │   (primary)       │   (detail views)       │
│ (48px) │   (flexible)      │   (flexible)           │
│        │                   │                        │
└────────┴───────────────────┴────────────────────────┘

Tablet (768-1024px):
┌────────┬───────────────────────────────────────────┐
│  Icon  │                                           │
│  Rail  │         Chat Pane (full)                   │
│        │    Canvas slides over from right           │
│        │                                           │
└────────┴───────────────────────────────────────────┘

Mobile (<768px):
┌───────────────────────────────────────────────────┐
│                                                   │
│              Chat (full screen)                    │
│         Tab/swipe to canvas                       │
│                                                   │
├───────────────────────────────────────────────────┤
│  Home  │  Projects  │  Workers  │  More           │
└───────────────────────────────────────────────────┘
```

## What to build

### 1. New AppShell component

Create `frontend/src/components/shell/AppShell.tsx`:
- Three-pane layout as described above
- Icon rail on the left (always visible on desktop/tablet, bottom nav on mobile)
- Chat pane as primary content area
- Canvas pane for detail views (collapsible, toggle via chat card clicks or rail nav)
- Responsive breakpoints: desktop >1024, tablet 768-1024, mobile <768
- State management: which pane is active (mobile), canvas content, rail selection

### 2. Icon rail

Create `frontend/src/components/shell/IconRail.tsx`:
- Vertical strip with icons: Home/Chat (MessageSquare), Projects (FolderKanban), Workers (Users), Documents (FileText), Reports (BarChart3), Settings (Settings)
- Active state indicator
- On click: either focuses chat with context ("show me projects") or opens a canvas list view
- On mobile: becomes bottom navigation bar
- Use lucide-react icons (already in deps)

### 3. Chat pane (promote from overlay to primary)

Create `frontend/src/components/shell/ChatPane.tsx`:
- Reuse ALL logic from `useChat` hook and the message rendering from `ChatPanel.tsx`
- Key additions vs current ChatPanel:
  - **Card rendering**: when a tool_result event arrives, render it as a rich card instead of plain text (see card system below)
  - **Conversation history**: a collapsible list of past conversations at the top or in a sidebar drawer
  - **Context indicator**: shows which project/entity the current conversation is about
  - **Action buttons in input area**: quick actions like "New project", "Daily log", "Check compliance"
- Remove the overlay/drawer mechanics — this is now a persistent pane, always visible

### 4. Canvas pane

Create `frontend/src/components/shell/CanvasPane.tsx`:
- Renders existing page components inside a constrained container
- Has its own header with: back button, breadcrumb, close button (returns to chat-only on mobile)
- Navigation driven by: clicking a card in chat, or clicking a rail item
- State: `{component: string, props: object}` — determines which existing page to render
- Wrap existing pages: they render as-is inside the canvas, with a max-width constraint

### 5. Card rendering system

Create `frontend/src/components/cards/` directory with card components:

Each card maps to a tool result type from the chat service:

| Card | Tool result | Key content |
|---|---|---|
| `ProjectSummaryCard` | `get_project_summary` | Project name, status, worker count, equipment count, 7-day activity |
| `ComplianceStatusCard` | `check_worker_compliance` / `check_project_compliance` | Compliance status, missing certs, expiring items |
| `DailyLogCard` | `get_daily_log_status` | Missing log dates, last 7 days status |
| `MorningBriefCard` | `generate_morning_brief` | Alerts, risk items, key actions |
| `WorkItemCard` | (new tools coming) | Description, state, cost estimate, assigned to |
| `InspectionCard` | (from tool results) | Date, category, pass/fail, score |
| `GenericEntityCard` | fallback | Title, key-value pairs, status badge |

Each card should:
- Have a compact view (shown inline in chat) and an expanded view (optional)
- Show a status badge, key metrics, and action buttons
- Have an "Open in canvas" button that navigates to the full detail view
- Use the existing ui/ primitives (Card, Badge, Button)

Create a `CardRenderer` component that takes a tool result JSON and selects the right card component based on tool name.

### 6. Routing update

Update `frontend/src/App.tsx`:
- Replace the current AppLayout-based routing with the new AppShell
- Auth routes (login, signup, etc.) stay as standalone full-screen pages
- All protected routes render inside AppShell
- Canvas navigation is state-based (not URL-based for now) — the URL reflects the conversation context, not the canvas page
- Keep the ability to deep-link to specific pages via URL for bookmarking

### 7. Mobile layout

- Chat is the default view on mobile
- Bottom nav bar with 4-5 items: Chat, Projects, Workers, Documents, More
- Tapping a rail item either focuses chat with context or pushes a full-screen canvas view
- Swipe gesture between chat and canvas (optional, can skip for MVP)
- All existing page components must work at mobile widths

## Design tokens (from index.css)

- Primary: `--machine: #F5B800` (yellow)
- Background: `#f4f5f3` (off-white)
- Fonts: IBM Plex Sans (body), IBM Plex Mono (labels/data)
- Radius: `0.1875rem` (3px) — tight, industrial
- Status colors: `--pass`, `--fail`, `--warn`
- Use existing Tailwind classes, do NOT introduce new CSS variables

## What NOT to do

- Do NOT rebuild the chat streaming logic — reuse `useChat` hook exactly
- Do NOT rebuild the voice hooks — they work, just wire them in later
- Do NOT rebuild the auth flow — Clerk integration stays as-is
- Do NOT rebuild the data hooks — useProjects, useWorkers, etc. stay as-is
- Do NOT rebuild the ui/ primitives — use them as-is
- Do NOT touch backend files — this is frontend only

## Testing

1. Desktop: three-pane layout renders correctly, icon rail visible, chat pane shows messages, canvas opens on card click
2. Mobile: chat is full screen, bottom nav works, canvas pushes as full-screen view
3. Send a chat message → verify streaming works in new ChatPane
4. Tool result → verify card renders inline in chat
5. Click card → verify canvas opens with correct detail view
6. Navigate via icon rail → verify correct view opens
