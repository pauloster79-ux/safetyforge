import * as React from "react"
import { cn } from "@/lib/utils"

type KerfMarkProps = React.ComponentProps<"div"> & {
  variant?: "full" | "mark" | "wordmark"
  size?: "sm" | "default" | "lg"
}

export function KerfMark({
  className,
  variant = "full",
  size = "default",
  ...props
}: KerfMarkProps) {
  const plateSize =
    size === "sm" ? "h-5 w-5 text-[11px]" :
    size === "lg" ? "h-8 w-8 text-[18px]" :
    "h-6 w-6 text-[13px]"

  const wordSize =
    size === "sm" ? "text-[10px]" :
    size === "lg" ? "text-[15px]" :
    "text-[12px]"

  return (
    <div
      data-slot="kerf-mark"
      data-variant={variant}
      className={cn("inline-flex items-center gap-2", className)}
      {...props}
    >
      {variant !== "wordmark" && (
        <div
          data-slot="kerf-mark-plate"
          className={cn(
            "inline-flex items-center justify-center rounded-[2px]",
            "bg-[var(--machine)] text-[var(--primary-foreground)]",
            "font-mono font-bold",
            "shadow-[inset_0_1px_0_rgba(255,255,255,0.25),inset_0_-1px_0_rgba(0,0,0,0.15)]",
            plateSize
          )}
        >
          K
        </div>
      )}
      {variant !== "mark" && (
        <span
          data-slot="kerf-mark-word"
          className={cn(
            "font-mono font-semibold uppercase tracking-[0.14em]",
            "text-foreground",
            wordSize
          )}
        >
          KERF
        </span>
      )}
    </div>
  )
}
