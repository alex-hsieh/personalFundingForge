import { ForgeEvent } from "@/hooks/use-forge-stream";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Cpu, Activity, CheckCircle2, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

export function AgenticChat({
  events,
  connected,
  done,
  error,
}: {
  events: ForgeEvent[];
  connected: boolean;
  done: boolean;
  error: string | null;
}) {
  const status = error ? "error" : done ? "done" : connected ? "live" : "idle";

  return (
    <Card className="ff-grain rounded-2xl border border-border/60 bg-card/35 backdrop-blur">
      <div className="flex items-center justify-between gap-2 border-b border-border/60 p-4">
        <div className="flex items-center gap-2">
          <div className="rounded-xl border border-border/60 bg-background/25 p-2">
            <Cpu className="h-4 w-4 text-accent" />
          </div>
          <div>
            <div className="text-sm font-semibold">Agentic Chat</div>
            <div className="text-xs text-muted-foreground">Explaining each step as it happens</div>
          </div>
        </div>

        <Badge
          variant="secondary"
          className={cn(
            "border border-border/60",
            status === "live" && "bg-emerald-500/15 text-emerald-200 border-emerald-500/20",
            status === "done" && "bg-accent/18 text-accent-foreground border-accent/25",
            status === "error" && "bg-rose-500/15 text-rose-200 border-rose-500/20",
          )}
        >
          {status === "live" && (
            <>
              <Activity className="mr-1.5 h-3.5 w-3.5" />
              Live
            </>
          )}
          {status === "done" && (
            <>
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
              Complete
            </>
          )}
          {status === "error" && (
            <>
              <WifiOff className="mr-1.5 h-3.5 w-3.5" />
              Error
            </>
          )}
          {status === "idle" && "Ready"}
        </Badge>
      </div>

      <ScrollArea className="h-[340px] md:h-[520px]">
        <div className="p-4 space-y-3">
          {error && (
            <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-sm">
              <div className="font-semibold">Stream failed</div>
              <div className="mt-1 text-rose-100/80">{error}</div>
            </div>
          )}

          {events.length === 0 && !error ? (
            <div className="rounded-xl border border-border/60 bg-background/20 p-3 text-sm text-muted-foreground">
              Start forging to see the live reasoning steps appear here.
            </div>
          ) : (
            events.map((e, idx) => (
              <div key={idx} className="rounded-xl border border-border/60 bg-background/20 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="text-sm">
                    <span className="font-semibold">Agent</span>{" "}
                    <span className="text-muted-foreground">·</span>{" "}
                    <span className="text-muted-foreground">Step {idx + 1}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">{e.done ? "final" : "working"}</div>
                </div>
                <div className="mt-2 text-sm leading-relaxed">{e.step}</div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
