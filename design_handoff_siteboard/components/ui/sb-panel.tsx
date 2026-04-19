/**
 * Site Board — SbPanel  (NEW primitive)
 *
 * A Card variant with a stamped header bar running across the top — used for
 * section blocks like "Work Items", "Payment Milestones", "Retention".
 *
 * Location: frontend/src/components/ui/sb-panel.tsx
 *
 * Structure:
 *   ┌─── [NumPlate] ── HEADER (kicker + title + actions) ───────┐
 *   │  body...                                                   │
 *   └────────────────────────────────────────────────────────────┘
 *
 * Usage:
 *   <SbPanel
 *     num="03"
 *     kicker="Section 03"
 *     title="Payment Milestones"
 *     actions={<Button size="xs" variant="ghost">Edit</Button>}
 *   >
 *     ...body content (table, form, etc.)
 *   </SbPanel>
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { NumPlate } from "./num-plate"

type SbPanelProps = React.ComponentProps<"section"> & {
  /** Two-character section number, e.g. "01" */
  num?: string
  /** Small uppercase line above the title, e.g. "Section 03" */
  kicker?: string
  /** Panel title */
  title: React.ReactNode
  /** Right-aligned controls in the header */
  actions?: React.ReactNode
  /** Controls the header chrome — "stamped" (default) or "plain" */
  chrome?: "stamped" | "plain"
  /** Animate in on mount (adds data-sb-beat). Pair with --beat-idx. */
  beat?: number
}

export function SbPanel({
  className,
  num,
  kicker,
  title,
  actions,
  chrome = "stamped",
  beat,
  children,
  style,
  ...props
}: SbPanelProps) {
  const beatStyle = beat !== undefined
    ? ({ ...style, ["--beat-idx" as string]: beat } as React.CSSProperties)
    : style

  return (
    <section
      data-slot="sb-panel"
      data-sb-beat={beat !== undefined ? "" : undefined}
      className={cn(
        "relative overflow-hidden",
        "bg-[var(--sb-ink-2)] text-card-foreground",
        "border border-[var(--border)] rounded-[var(--radius)]",
        "shadow-[inset_0_1px_0_var(--sb-plate-highlight)]",
        className
      )}
      style={beatStyle}
      {...props}
    >
      <header
        data-slot="sb-panel-header"
        className={cn(
          "flex items-center gap-3 px-3 h-10",
          "border-b border-[var(--sb-hairline)]",
          chrome === "stamped" && [
            "bg-[var(--sb-ink-4)]",
            "shadow-[inset_0_1px_0_var(--sb-plate-highlight),inset_0_-1px_0_var(--sb-plate-recess)]",
          ]
        )}
      >
        {num ? <NumPlate size="sm">{num}</NumPlate> : null}

        <div className="flex min-w-0 flex-1 items-baseline gap-2">
          {kicker ? (
            <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
              {kicker}
            </span>
          ) : null}
          <h3 className="truncate text-[13px] font-medium text-foreground">
            {title}
          </h3>
        </div>

        {actions ? (
          <div className="flex shrink-0 items-center gap-1">{actions}</div>
        ) : null}
      </header>

      <div data-slot="sb-panel-body">{children}</div>
    </section>
  )
}
