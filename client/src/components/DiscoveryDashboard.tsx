import { useMemo, useState } from "react";
import { useGrants } from "@/hooks/use-grants";
import { Grant } from "@shared/schema";
import { GrantCard } from "@/components/GrantCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, SlidersHorizontal, ArrowRight, RefreshCw, FileX2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function DiscoveryDashboard({
  profileSummary,
  onPickGrant,
  selectedGrantId,
}: {
  profileSummary: { role: string; year: string; program: string };
  selectedGrantId: number | null;
  onPickGrant: (grant: Grant) => void;
}) {
  const { data, isLoading, error, refetch, isFetching } = useGrants();
  const [query, setQuery] = useState("");
  const [audience, setAudience] = useState<"All" | "Faculty" | "Grad Students" | "Undergrads">("All");

  const grants = data ?? [];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return grants
      .filter((g) => (audience === "All" ? true : g.targetAudience === audience))
      .filter((g) => {
        if (!q) return true;
        return (
          g.name.toLowerCase().includes(q) ||
          g.matchCriteria.toLowerCase().includes(q) ||
          g.eligibility.toLowerCase().includes(q)
        );
      });
  }, [audience, grants, query]);

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 10, filter: "blur(10px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.55, ease: [0.2, 0.9, 0.2, 1] }}
        className="pt-8 md:pt-10"
      >
        <div className="grid gap-6 lg:grid-cols-[1fr_0.4fr] lg:items-start">
          <div>
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between md:gap-6">
              <div>
                <h2 className="text-2xl sm:text-3xl">Discovery Dashboard</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Filter grants by audience, search keywords, then select one to forge a packet.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="border border-border/60">
                  Role: <span className="ml-1 font-semibold">{profileSummary.role}</span>
                </Badge>
                <Badge variant="secondary" className="border border-border/60">
                  Level: <span className="ml-1 font-semibold">{profileSummary.year}</span>
                </Badge>
                <Badge variant="secondary" className="border border-border/60">
                  Program: <span className="ml-1 font-semibold">{profileSummary.program}</span>
                </Badge>
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-[1fr_auto_auto] md:items-center">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search grants, criteria, eligibility…"
                  className="pl-9 bg-background/35"
                  type="search"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant={audience === "All" ? "default" : "secondary"}
                  onClick={() => setAudience("All")}
                  className={cn(audience === "All" ? "bg-primary text-primary-foreground" : "border border-border/60")}
                >
                  All
                </Button>
                <Button
                  variant={audience === "Faculty" ? "default" : "secondary"}
                  onClick={() => setAudience("Faculty")}
                  className={cn(audience === "Faculty" ? "bg-primary text-primary-foreground" : "border border-border/60")}
                >
                  Faculty
                </Button>
                <Button
                  variant={audience === "Grad Students" ? "default" : "secondary"}
                  onClick={() => setAudience("Grad Students")}
                  className={cn(audience === "Grad Students" ? "bg-primary text-primary-foreground" : "border border-border/60")}
                >
                  Grad
                </Button>
                <Button
                  variant={audience === "Undergrads" ? "default" : "secondary"}
                  onClick={() => setAudience("Undergrads")}
                  className={cn(audience === "Undergrads" ? "bg-primary text-primary-foreground" : "border border-border/60")}
                >
                  Undergrad
                </Button>
              </div>

              <div className="flex items-center gap-2 justify-end">
                <Button variant="secondary" onClick={() => setQuery("")} className="border border-border/60">
                  <SlidersHorizontal className="mr-2 h-4 w-4" />
                  Clear
                </Button>
                <Button variant="secondary" onClick={() => refetch()} className="border border-border/60" disabled={isFetching}>
                  <RefreshCw className={cn("mr-2 h-4 w-4", isFetching ? "animate-spin" : "")} />
                  Refresh
                </Button>
              </div>
            </div>

            <div className="mt-6">
              {isLoading ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <Card
                      key={i}
                      className="rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur"
                    >
                      <Skeleton className="h-5 w-40" />
                      <Skeleton className="mt-3 h-4 w-52" />
                      <Skeleton className="mt-5 h-16 w-full" />
                      <Skeleton className="mt-4 h-10 w-full" />
                    </Card>
                  ))}
                </div>
              ) : error ? (
                <Card className="rounded-2xl border border-border/60 bg-card/35 p-6 backdrop-blur">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-lg font-semibold">Couldn’t load grants</div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {(error as Error)?.message || "Unknown error"}
                      </p>
                    </div>
                    <Button onClick={() => refetch()} className="bg-accent text-accent-foreground border border-accent/30">
                      Try again
                    </Button>
                  </div>
                </Card>
              ) : filtered.length === 0 ? (
                <Card className="rounded-2xl border border-border/60 bg-card/35 p-8 backdrop-blur">
                  <div className="flex flex-col items-center text-center">
                    <div className="rounded-2xl border border-border/60 bg-background/30 p-3">
                      <FileX2 className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <div className="mt-3 text-lg font-semibold">No matches found</div>
                    <p className="mt-1 max-w-md text-sm text-muted-foreground">
                      Try a different keyword or broaden the audience filter.
                    </p>
                    <div className="mt-4 flex items-center gap-2">
                      <Button variant="secondary" onClick={() => setQuery("")} className="border border-border/60">
                        Reset search
                      </Button>
                      <Button onClick={() => setAudience("All")} className="bg-accent text-accent-foreground border border-accent/30">
                        Show all
                      </Button>
                    </div>
                  </div>
                </Card>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {filtered.map((g) => (
                    <GrantCard
                      key={g.id}
                      grant={g}
                      selected={selectedGrantId === g.id}
                      onSelect={onPickGrant}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          <Card className="ff-grain rounded-2xl border border-border/60 bg-card/35 p-6 backdrop-blur lg:sticky lg:top-28">
            <div className="text-sm font-semibold">Next step</div>
            <p className="mt-1 text-sm text-muted-foreground">
              Select a grant to start forging the packet. You’ll see each agent step streamed live.
            </p>

            <div className="mt-5 rounded-xl border border-border/60 bg-background/25 p-4">
              <div className="text-xs text-muted-foreground">Tip</div>
              <div className="mt-1 text-sm">
                Look for the <span className="font-semibold">FSU internal deadline</span> badge and the compliance preview.
              </div>
            </div>

            <Button
              onClick={() => {
                // This button exists to avoid dead UI; it nudges users to click a card.
                const first = filtered[0];
                if (first) onPickGrant(first);
              }}
              disabled={filtered.length === 0}
              className="mt-5 w-full bg-accent text-accent-foreground border border-accent/30 shadow-lg shadow-accent/15"
            >
              Pick the top match
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>

            <p className="mt-3 text-xs text-muted-foreground">
              This is a deterministic “smart default” based on your current filters.
            </p>
          </Card>
        </div>

        <div className="pb-10 md:pb-14" />
      </motion.div>
    </div>
  );
}
