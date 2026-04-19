import * as React from "react"
import { cn } from "@/lib/utils"

type TypingIndicatorProps = React.ComponentProps<"div"> & {
  /** Override the label. Default: "KERF IS TYPING" */
  label?: string
}

export function TypingIndicator({
  className,
  label = "KERF IS TYPING",
  ...props
}: TypingIndicatorProps) {
  return (
    <div
      data-slot="typing-indicator"
      className={cn(
        "inline-flex items-center gap-2",
        "font-mono text-[10px] uppercase tracking-[0.12em]",
        "text-muted-foreground",
        className
      )}
      aria-live="polite"
      aria-label={`${label.toLowerCase()}…`}
      {...props}
    >
      <span className="sb-typing-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span className="sb-caret">{label}</span>
    </div>
  )
}
