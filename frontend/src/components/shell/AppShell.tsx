/**
 * AppShell — conversational-first three-pane layout.
 *
 * Desktop (>1024px):  IconRail (48px) | ChatPane (flexible) | CanvasPane (flexible)
 * Tablet (768-1024):  IconRail (48px) | ChatPane (full) — canvas slides over
 * Mobile (<768px):    Chat (full) | Canvas (full) — bottom nav bar
 *
 * Wraps the JurisdictionProvider and manages the ShellContext.
 */

import { JurisdictionProvider } from '@/contexts/JurisdictionContext';
import { ShellContext, useShellState } from '@/hooks/useShell';
import { IconRail } from './IconRail';
import { ChatPane } from './ChatPane';
import { CanvasPane } from './CanvasPane';
import { DemoUserSwitcher } from '@/components/dev/DemoUserSwitcher';

export function AppShell() {
  const shellState = useShellState();

  return (
    <JurisdictionProvider>
      <ShellContext.Provider value={shellState}>
        <div className="flex h-screen bg-background">
          {/* Icon rail — hidden on mobile (bottom nav instead) */}
          {shellState.breakpoint !== 'mobile' && <IconRail />}

          {/* Main content area */}
          {shellState.breakpoint === 'mobile' ? (
            /* Mobile: show one pane at a time */
            <div className="flex flex-1 flex-col pb-14">
              {shellState.mobilePane === 'chat' ? <ChatPane /> : null}
              <CanvasPane />
              <IconRail />
            </div>
          ) : shellState.breakpoint === 'tablet' ? (
            /* Tablet: chat full width, canvas overlays from right */
            <div className="relative flex flex-1">
              <div className="flex-1">
                <ChatPane />
              </div>
              {shellState.canvasOpen && (
                <div className="absolute inset-y-0 right-0 w-[60%] shadow-xl">
                  <CanvasPane />
                </div>
              )}
            </div>
          ) : (
            /* Desktop: side-by-side split */
            <div className="flex flex-1">
              <div
                className={`flex flex-col ${
                  shellState.canvasOpen ? 'w-[40%] min-w-[360px]' : 'flex-1'
                } transition-all duration-200`}
              >
                <ChatPane />
              </div>
              {shellState.canvasOpen && (
                <div className="flex-1 min-w-[400px]">
                  <CanvasPane />
                </div>
              )}
            </div>
          )}
          {/* DemoUserSwitcher now lives inside ChatPane header */}
        </div>
      </ShellContext.Provider>
    </JurisdictionProvider>
  );
}
