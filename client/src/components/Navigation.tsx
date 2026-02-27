import React from 'react';
import { motion } from 'framer-motion';
import logoUrl from '@assets/FundingForge_Logo_1772196329334.png';
import { ShieldAlert } from 'lucide-react';

export function Navigation() {
  return (
    <motion.nav 
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="fixed top-0 left-0 right-0 z-50 px-6 py-4 pointer-events-none"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between pointer-events-auto">
        <div className="flex items-center gap-3 bg-black/20 backdrop-blur-md border border-white/5 rounded-2xl p-2 pr-6 shadow-2xl">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary/40 flex items-center justify-center p-1.5 shadow-[0_0_15px_rgba(120,40,31,0.5)]">
            <img src={logoUrl} alt="FundingForge Logo" className="w-full h-full object-contain filter drop-shadow-md" />
          </div>
          <div className="flex flex-col">
            <span className="font-display font-bold text-lg leading-none tracking-wide text-foreground">
              Funding<span className="text-accent">Forge</span>
            </span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold">
              Florida State University
            </span>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-2 bg-black/20 backdrop-blur-md border border-white/5 rounded-full px-4 py-2 text-xs font-medium text-muted-foreground">
          <ShieldAlert className="w-4 h-4 text-accent" />
          <span>RAMP Compliance Network Active</span>
        </div>
      </div>
    </motion.nav>
  );
}
