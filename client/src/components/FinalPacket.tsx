import { Grant } from "@shared/schema";
import { useFaculty } from "@/hooks/use-faculty";
import { useForgeStream } from "@/hooks/use-forge-stream";
import { AgenticChat } from "@/components/AgenticChat";
import { ProposalDraft } from "@/components/ProposalDraft";
import { CollaboratorMesh } from "@/components/CollaboratorMesh";
import { RampChecklist } from "@/components/RampChecklist";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Flame, RefreshCw, Zap } from "lucide-react";
import { useMemo, useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { motion } from "framer-motion";

export function FinalPacket({
  grant,
  profile,
  onBack,
  onReset,
}: {
  grant: Grant;
  profile: { role: string; year: string; program: string };
  onBack: () => void;
  onReset: () => void;
}) {
  const { toast } = useToast();
  const [streamEnabled, setStreamEnabled] = useState(true);

  const { events, connected, done, error, cancel } = useForgeStream(grant.id, streamEnabled);

  const { data: faculty, isLoading: facultyLoading, error: facultyError, refetch: refetchFaculty, isFetching } =
    useFaculty();

  const topFaculty = useMemo(() => (faculty ?? []).slice(0, 3), [faculty]);

  const restartForge = () => {
    cancel();
    setStreamEnabled(false);
    // allow effect to re-run
    setTimeout(() => setStreamEnabled(true), 50);
  };

  const ping = (person: any) => {
    toast({
      title: "Ping queued",
      description: `Prepared a collaborator outreach message for ${person.name} (mock action).`,
    });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 10, filter: "blur(10px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.55, ease: [0.2, 0.9, 0.2, 1] }}
        className="pt-8 md:pt-10"
      >
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between md:gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-primary text-primary-foreground border border-primary/30">
                Final Packet
              </Badge>
              <Badge variant="secondary" className="border border-border/60">
                {grant.name}
              </Badge>
              <Badge variant="secondary" className="border border-border/60">
                {profile.role} · {profile.year} · {profile.program}
              </Badge>
            </div>
            <h2 className="mt-3 text-2xl sm:text-3xl">Forging output</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Streamed steps show what’s happening; once complete, your packet sections unlock.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button variant="secondary" className="border border-border/60" onClick={onBack}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to discovery
            </Button>

            <Button
              variant="secondary"
              className="border border-border/60"
              onClick={() => {
                restartForge();
                toast({ title: "Re-forging", description: "Restarted the stream for this grant." });
              }}
            >
              <Flame className="mr-2 h-4 w-4" />
              Re-forge
            </Button>

            <Button onClick={onReset} className="bg-accent text-accent-foreground border border-accent/30">
              <Zap className="mr-2 h-4 w-4" />
              New profile
            </Button>
          </div>
        </div>

        <div className="mt-6">
          <div className="space-y-6">
            <Card className="ff-grain rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold">Forging status</div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {error
                      ? "The stream encountered an issue. You can re-forge or continue with the draft scaffold."
                      : done
                        ? "Complete — packet sections are ready."
                        : connected
                          ? "Live — steps streaming now."
                          : "Initializing…"}
                  </p>
                </div>
                <Badge
                  variant="secondary"
                  className="border border-border/60 bg-background/25"
                >
                  {done ? "done" : connected ? "streaming" : "pending"}
                </Badge>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <Button
                  variant="secondary"
                  className="border border-border/60"
                  onClick={() => {
                    cancel();
                    setStreamEnabled(false);
                    toast({ title: "Stream stopped", description: "You can re-forge anytime." });
                  }}
                  disabled={!connected && !streamEnabled}
                >
                  Stop stream
                </Button>

                <Button
                  onClick={restartForge}
                  className="bg-accent text-accent-foreground border border-accent/30"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Restart stream
                </Button>
              </div>
            </Card>

            <ProposalDraft grantName={grant.name} profile={profile} done={done} />

            {facultyLoading ? (
              <Card className="rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-5 w-44" />
                  <Skeleton className="h-6 w-20" />
                </div>
                <Skeleton className="mt-4 h-16 w-full" />
                <Skeleton className="mt-3 h-16 w-full" />
                <Skeleton className="mt-3 h-16 w-full" />
              </Card>
            ) : facultyError ? (
              <Card className="rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur">
                <div className="text-sm font-semibold">Couldn’t load collaborators</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {(facultyError as Error)?.message || "Unknown error"}
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <Button
                    className="bg-accent text-accent-foreground border border-accent/30"
                    onClick={() => refetchFaculty()}
                    disabled={isFetching}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Retry
                  </Button>
                </div>
              </Card>
            ) : (
              <CollaboratorMesh faculty={topFaculty} onPing={ping} />
            )}

            <RampChecklist />
          </div>
        </div>

        <div className="pb-10 md:pb-14" />
      </motion.div>
    </div>
  );
}
