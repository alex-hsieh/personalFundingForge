import { useState } from "react";
import { motion } from "framer-motion";
import { GlassCard } from "./ui/glass-card";
import { GlowButton } from "./ui/glow-button";
import { Sparkles, Cpu, GraduationCap, ChevronRight } from "lucide-react";

interface IntakeFormProps {
  onComplete: () => void;
}

export function IntakeForm({ onComplete }: IntakeFormProps) {
  const [role, setRole] = useState("");
  const [year, setYear] = useState("");
  const [program, setProgram] = useState("");

  const isComplete = role && year && program;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 1.05, y: -20 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="max-w-2xl mx-auto w-full"
    >
      <div className="text-center mb-10">
        <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
          Discover Your <span className="text-primary text-glow">Funding</span>
        </h1>
        <p className="text-lg text-white/60 font-light">
          Configure your academic profile to let the AI Forge find high-impact grants tailored to you.
        </p>
      </div>

      <GlassCard className="p-8 md:p-10 relative overflow-hidden">
        {/* Decorative background element */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-64 h-64 bg-secondary/20 blur-3xl rounded-full pointer-events-none" />
        
        <div className="space-y-8 relative z-10">
          <div className="space-y-4">
            <label className="block text-sm font-medium text-white/80 uppercase tracking-wider">
              1. Primary Role
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {['Undergrad', 'PhD Student', 'Faculty'].map((r) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`p-4 rounded-xl border transition-all duration-200 flex flex-col items-center gap-2 ${
                    role === r 
                      ? 'bg-primary/20 border-primary text-primary' 
                      : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'
                  }`}
                >
                  {r === 'Faculty' ? <Cpu className="w-6 h-6" /> : <GraduationCap className="w-6 h-6" />}
                  <span className="font-medium">{r}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <label className="block text-sm font-medium text-white/80 uppercase tracking-wider">
              2. Academic Year / Level
            </label>
            <select 
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            >
              <option value="" disabled className="text-black">Select your level...</option>
              <option value="freshman" className="text-black">Freshman / Sophomore</option>
              <option value="junior" className="text-black">Junior / Senior</option>
              <option value="early_phd" className="text-black">Years 1-3 PhD</option>
              <option value="late_phd" className="text-black">Years 4+ PhD</option>
              <option value="pre_tenure" className="text-black">Pre-Tenure Faculty</option>
              <option value="tenured" className="text-black">Tenured Faculty</option>
            </select>
          </div>

          <div className="space-y-4">
            <label className="block text-sm font-medium text-white/80 uppercase tracking-wider">
              3. College / Program
            </label>
            <input 
              type="text"
              value={program}
              onChange={(e) => setProgram(e.target.value)}
              placeholder="e.g. College of Arts and Sciences, Engineering..."
              className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            />
          </div>

          <div className="pt-6">
            <GlowButton 
              className="w-full py-5 text-xl" 
              disabled={!isComplete}
              onClick={onComplete}
            >
              <Sparkles className="w-5 h-5" />
              Forge My Profile
              <ChevronRight className="w-5 h-5 ml-2" />
            </GlowButton>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
