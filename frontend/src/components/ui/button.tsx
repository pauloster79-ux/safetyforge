import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  [
    "group/button inline-flex shrink-0 items-center justify-center",
    "rounded-[3px] border border-transparent bg-clip-padding",
    "text-sm font-medium whitespace-nowrap",
    "transition-all duration-[120ms] ease-out outline-none select-none",
    "focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
    "active:not-aria-[haspopup]:translate-y-px",
    "disabled:pointer-events-none disabled:opacity-50",
    "aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20",
    "dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-primary text-primary-foreground",
          "shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]",
          "hover:bg-[var(--machine-dark)]",
          "[a]:hover:bg-[var(--machine-dark)]",
        ].join(" "),
        outline: [
          "border-border bg-background text-foreground",
          "hover:bg-sb-ink-3 hover:text-foreground",
          "aria-expanded:bg-sb-ink-3 aria-expanded:text-foreground",
          "dark:border-input dark:bg-sb-ink-2 dark:hover:bg-sb-ink-3",
        ].join(" "),
        secondary: [
          "bg-secondary text-secondary-foreground",
          "hover:bg-secondary/80",
          "aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",
        ].join(" "),
        ghost: [
          "text-foreground",
          "hover:bg-[color-mix(in_oklab,var(--machine)_6%,transparent)] hover:text-foreground",
          "aria-expanded:bg-muted aria-expanded:text-foreground",
        ].join(" "),
        destructive: [
          "bg-destructive/10 text-destructive",
          "hover:bg-destructive/20",
          "focus-visible:border-destructive/40 focus-visible:ring-destructive/20",
          "dark:bg-destructive/20 dark:hover:bg-destructive/30",
          "dark:focus-visible:ring-destructive/40",
        ].join(" "),
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default:
          "h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        xs: "h-6 gap-1 rounded-[3px] px-2 text-xs has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-7 gap-1 rounded-[3px] px-2.5 text-[0.8rem] has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-9 gap-1.5 px-3 has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3",
        icon: "size-8",
        "icon-xs":
          "size-6 rounded-[3px] [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-7 rounded-[3px]",
        "icon-lg": "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  render,
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...(render ? { render, nativeButton: false } : {})}
      {...props}
    />
  )
}

export { Button, buttonVariants }
