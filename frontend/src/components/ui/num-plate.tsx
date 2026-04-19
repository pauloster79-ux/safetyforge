import * as React from "react"
import { cn } from "@/lib/utils"

type NumPlateProps = React.ComponentProps<"div"> & {
  /**
   * "stamped" (default) — debossed ink plate with subtle top highlight.
   * "machine" — yellow face for milestone numbers.
   */
  variant?: "stamped" | "machine"
  size?: "sm" | "default" | "lg"
  children: React.ReactNode
}

export function NumPlate({
  className,
  variant = "stamped",
  size = "default",
  children,
  ...props
}: NumPlateProps) {
  return (
    <div
      data-slot="num-plate"
      data-variant={variant}
      className={cn(
        "inline-flex items-center justify-center",
        "font-mono font-semibold tracking-[0.08em]",
        "rounded-[2px]",
        "tabular-nums",

        size === "sm" && "h-5 min-w-6 px-1 text-[10px]",
        size === "default" && "h-6 min-w-7 px-1.5 text-[11px]",
        size === "lg" && "h-8 min-w-10 px-2 text-[13px]",

        variant === "stamped" && [
          "bg-[var(--sb-ink-3)] text-muted-foreground",
          "border border-[var(--sb-hairline)]",
          "shadow-[inset_0_1px_0_var(--sb-plate-highlight),inset_0_-1px_0_var(--sb-plate-recess)]",
        ],

        variant === "machine" && [
          "bg-[var(--machine)] text-[var(--primary-foreground)]",
          "shadow-[inset_0_1px_0_rgba(255,255,255,0.25),inset_0_-1px_0_rgba(0,0,0,0.15)]",
        ],

        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
