import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center px-2.5 py-0.5 text-xs font-mono font-medium border transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary/10 text-primary border-primary/30",
        secondary: "bg-secondary text-secondary-foreground border-secondary",
        destructive: "bg-destructive/10 text-destructive border-destructive/30",
        outline: "text-foreground border-foreground",
        success: "bg-[#6Ec85c]/10 text-[#6Ec85c] border-[#6Ec85c]/30",
        warning: "bg-[#faad14]/10 text-[#faad14] border-[#faad14]/30",
        orange: "bg-[#FF5300]/10 text-[#FF5300] border-[#FF5300]/30",
        purple: "bg-[#D4A0FF]/10 text-[#D4A0FF] border-[#D4A0FF]/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({ className, variant, ...props }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
