/**
 * Site Board — Badge
 *
 * Replaces frontend/src/components/ui/badge.tsx
 *
 * Changes vs existing:
 *   • Added semantic `pass / fail / warn` variants using your existing tokens
 *   • Tighter — h-5 / px-2 / text-[11px] with uppercase letter-spacing
 *   • Radius reduced from 4xl (pill) to lg (small pill) for ledger feel
 *   • Default keeps yellow; use sparingly — max one per row
 */

import { mergeProps } from "@base-ui/react/merge-props"
import { useRender } from "@base-ui/react/use-render"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  [
    "group/badge inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1",
    "overflow-hidden border border-transparent",
    "px-2 py-0.5 rounded-[var(--radius-lg)]",
    "text-[11px] font-medium uppercase tracking-[0.06em] whitespace-nowrap",
    "transition-colors duration-[120ms]",
    "focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50",
    "has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5",
    "aria-invalid:border-destructive aria-invalid:ring-destructive/20",
    "dark:aria-invalid:ring-destructive/40",
    "[&>svg]:pointer-events-none [&>svg]:size-3!",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground [a]:hover:bg-primary/80",
        secondary:
          "bg-secondary text-secondary-foreground [a]:hover:bg-secondary/80",
        outline:
          "border-border text-foreground [a]:hover:bg-muted [a]:hover:text-muted-foreground",
        ghost:
          "text-muted-foreground hover:bg-muted hover:text-foreground dark:hover:bg-muted/50",

        // NEW: semantic variants
        pass:
          "bg-[var(--pass-bg)] text-[var(--pass)] border-[color-mix(in_oklab,var(--pass)_30%,transparent)]",
        fail:
          "bg-[var(--fail-bg)] text-[var(--fail)] border-[color-mix(in_oklab,var(--fail)_30%,transparent)]",
        warn:
          "bg-[var(--warn-bg)] text-[var(--warn)] border-[color-mix(in_oklab,var(--warn)_30%,transparent)]",
        info:
          "bg-sb-ink-3 text-muted-foreground border-[var(--sb-hairline)]",

        destructive:
          "bg-destructive/10 text-destructive focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:focus-visible:ring-destructive/40 [a]:hover:bg-destructive/20",
        link: "text-primary underline-offset-4 hover:underline",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  render,
  ...props
}: useRender.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return useRender({
    defaultTagName: "span",
    props: mergeProps<"span">(
      {
        className: cn(badgeVariants({ variant }), className),
      },
      props
    ),
    render,
    state: {
      slot: "badge",
      variant,
    },
  })
}

export { Badge, badgeVariants }
