import { Grant } from "@shared/schema";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CalendarClock, ChevronRight, Shield } from "lucide-react";
import { motion } from "framer-motion";
import { useMemo } from "react";

function seededScore(id: number) {
  // deterministic 85-98
  const base = 85;
  const mod = (id * 7) % 14; // 0..13
  return base + mod;
}

type ComplianceLight = "green" | "yellow" | "red";

function compliancePreview(id: number): { label: string; state: ComplianceLight }[] {
  const items = [
    { label: "IRB", state: "green" as const },
    { label: "COI", state: "yellow" as const },
    { label: "Data", state: "green" as const },
  ];
  // nudge one based on id
  const idx = id % items.length;
  const cycle: ComplianceLight[] = ["green", "yellow", "red"];
  items[idx] = { ...items[idx], state: cycle[(id + 1) % cycle.length] };
  return items;
}

export function GrantCard({
  grant,
  selected,
  onSelect,
}: {
  grant: Grant;
  selected?: boolean;
  onSelect: (grant: Grant) => void;
}) {
  const score = useMemo(() => seededScore(grant.id), [grant.id]);
  const lights = useMemo(() => compliancePreview(grant.id), [grant.id]);

  return (
    <motion.button
      onClick={() => onSelect(grant)}
      className="text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.995 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
    >
      <Card
        className={cn(
          "ff-grain group relative overflow-visible rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur",
          "transition-shadow duration-300",
          selected ? "ff-glow" : "",
        )}
      >
        <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-accent/10 via-primary/10 to-transparent opacity-0 blur-sm transition-opacity duration-300 group-hover:opacity-100" />

        <div className="relative flex items-start justify-between gap-3">
          <div>
            <div className="text-lg font-semibold leading-snug">{grant.name}</div>
            <div className="mt-1 text-sm text-muted-foreground">
              {grant.targetAudience} · {grant.eligibility}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="border border-border/60">
              <Shield className="mr-1.5 h-3.5 w-3.5 text-accent" />
              {score}%
            </Badge>
            <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform duration-300 group-hover:translate-x-0.5" />
          </div>
        </div>

        <div className="relative mt-4 flex flex-wrap items-center gap-2">
          <Badge className="bg-primary text-primary-foreground border border-primary/30">
            Match: {grant.matchCriteria}
          </Badge>
          <Badge variant="secondary" className="border border-border/60">
            <CalendarClock className="mr-1.5 h-3.5 w-3.5" />
            {grant.internalDeadline}
          </Badge>
        </div>

        <div className="relative mt-5 rounded-xl border border-border/60 bg-background/25 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs font-medium text-muted-foreground">Compliance preview</div>
            <div className="text-[11px] text-muted-foreground">Hover to reveal</div>
          </div>

          <div className="mt-2 flex gap-2">
            {lights.map((l) => (
              <div
                key={l.label}
                className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/30 px-2.5 py-1.5"
              >
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    l.state === "green" && "bg-emerald-500",
                    l.state === "yellow" && "bg-amber-400",
                    l.state === "red" && "bg-rose-500",
                  )}
                />
                <span className="text-xs">{l.label}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </motion.button>
  );
}
