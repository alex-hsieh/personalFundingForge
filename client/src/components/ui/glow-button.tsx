import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface GlowButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
}

export const GlowButton = forwardRef<HTMLButtonElement, GlowButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "relative px-8 py-4 rounded-xl font-display font-semibold text-lg overflow-hidden group transition-all duration-300",
          variant === "primary" 
            ? "bg-gradient-to-r from-primary to-[#b39e72] text-primary-foreground shadow-[0_0_20px_rgba(206,184,136,0.3)] hover:shadow-[0_0_35px_rgba(206,184,136,0.5)]"
            : "bg-gradient-to-r from-secondary to-[#5a1b14] text-secondary-foreground shadow-[0_0_20px_rgba(120,40,31,0.3)] hover:shadow-[0_0_35px_rgba(120,40,31,0.5)]",
          "disabled:opacity-50 disabled:cursor-not-allowed hover:-translate-y-0.5 active:translate-y-0",
          className
        )}
        {...props}
      >
        <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <span className="relative z-10 flex items-center justify-center gap-2">
          {props.children}
        </span>
      </button>
    );
  }
);

GlowButton.displayName = "GlowButton";
