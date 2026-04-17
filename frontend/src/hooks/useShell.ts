/**
 * Shell state management for the conversational-first layout.
 *
 * Tracks which pane is active (mobile), canvas content,
 * rail selection, and responsive breakpoints.
 */

import { createContext, useCallback, useContext, useEffect, useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type RailItem =
  | 'chat'
  | 'projects'
  | 'schedule'
  | 'daily-logs'
  | 'workers'
  | 'equipment'
  | 'safety'
  | 'documents'
  | 'reports'
  | 'queries'
  | 'knowledge'
  | 'settings';

export type MobilePane = 'chat' | 'canvas';

export type Breakpoint = 'mobile' | 'tablet' | 'desktop';

export interface CanvasView {
  /** Key identifying which page component to render */
  component: string;
  /** Props to pass to the page component */
  props: Record<string, unknown>;
  /** Human-readable label for the breadcrumb */
  label: string;
}

export interface ShellState {
  /** Currently highlighted rail item */
  activeRail: RailItem;
  /** What the canvas pane is showing (null = collapsed) */
  canvasView: CanvasView | null;
  /** Which pane is visible on mobile */
  mobilePane: MobilePane;
  /** Current responsive breakpoint */
  breakpoint: Breakpoint;
  /** Canvas is open (derived: canvasView !== null) */
  canvasOpen: boolean;
}

export interface ShellActions {
  /** Navigate to a canvas page (pushes onto history stack) */
  openCanvas: (view: CanvasView) => void;
  /** Go back to the previous canvas view (pops history stack). Closes if empty. */
  goBack: () => void;
  /** Close the canvas pane entirely and clear history */
  closeCanvas: () => void;
  /** Set the active rail item */
  setActiveRail: (item: RailItem) => void;
  /** Switch mobile pane */
  setMobilePane: (pane: MobilePane) => void;
  /** Open canvas from a tool result card */
  openCanvasFromCard: (component: string, props: Record<string, unknown>, label: string) => void;
  /** True when there's a previous view to go back to */
  canGoBack: boolean;
}

export type ShellContextValue = ShellState & ShellActions;

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

export const ShellContext = createContext<ShellContextValue | null>(null);

export function useShell(): ShellContextValue {
  const ctx = useContext(ShellContext);
  if (!ctx) throw new Error('useShell must be used within ShellProvider');
  return ctx;
}

// ---------------------------------------------------------------------------
// Hook that provides the state (used inside ShellProvider)
// ---------------------------------------------------------------------------

function getBreakpoint(): Breakpoint {
  if (typeof window === 'undefined') return 'desktop';
  const w = window.innerWidth;
  if (w < 768) return 'mobile';
  if (w < 1024) return 'tablet';
  return 'desktop';
}

export function useShellState(): ShellContextValue {
  const [activeRail, setActiveRail] = useState<RailItem>('chat');
  const [canvasView, setCanvasView] = useState<CanvasView | null>(null);
  const [history, setHistory] = useState<CanvasView[]>([]);
  const [mobilePane, setMobilePane] = useState<MobilePane>('chat');
  const [breakpoint, setBreakpoint] = useState<Breakpoint>(getBreakpoint);

  // Track window resize for breakpoint
  useEffect(() => {
    const onResize = () => setBreakpoint(getBreakpoint());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const openCanvas = useCallback(
    (view: CanvasView) => {
      setCanvasView((prev) => {
        // Push the current view onto history when navigating somewhere new.
        // Avoid pushing duplicates when re-opening the same view.
        if (prev && (prev.component !== view.component || JSON.stringify(prev.props) !== JSON.stringify(view.props))) {
          setHistory((h) => [...h, prev]);
        }
        return view;
      });
      if (breakpoint === 'mobile') {
        setMobilePane('canvas');
      }
    },
    [breakpoint],
  );

  const goBack = useCallback(() => {
    setHistory((h) => {
      if (h.length === 0) {
        // No history — close the canvas.
        setCanvasView(null);
        setMobilePane('chat');
        return h;
      }
      const prev = h[h.length - 1];
      setCanvasView(prev);
      return h.slice(0, -1);
    });
  }, []);

  const closeCanvas = useCallback(() => {
    setCanvasView(null);
    setHistory([]);
    setMobilePane('chat');
  }, []);

  const openCanvasFromCard = useCallback(
    (component: string, props: Record<string, unknown>, label: string) => {
      openCanvas({ component, props, label });
    },
    [openCanvas],
  );

  return {
    activeRail,
    canvasView,
    mobilePane,
    breakpoint,
    canvasOpen: canvasView !== null,
    canGoBack: history.length > 0,
    openCanvas,
    goBack,
    closeCanvas,
    setActiveRail,
    setMobilePane,
    openCanvasFromCard,
  };
}
