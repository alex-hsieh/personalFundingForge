import { HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, interactive = false, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "glass-panel rounded-2xl overflow-hidden",
          interactive && "glass-panel-hover cursor-pointer",
          className
        )}
        {...props}
      />
    );
  }
);

GlassCard.displayName = "GlassCard";
