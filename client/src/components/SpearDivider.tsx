import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function SpearDivider({ className }: { className?: string }) {
  return (
    <div className={cn("w-full h-px relative flex items-center justify-center my-8", className)}>
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-border to-transparent" />
      <div className="absolute w-24 h-1 bg-accent spear-divider opacity-50 shadow-[0_0_10px_rgba(206,184,136,0.5)]" />
    </div>
  );
}
