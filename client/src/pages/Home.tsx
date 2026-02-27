import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SelectionPortal, type IntakeProfile } from "@/components/SelectionPortal";
import { DiscoveryDashboard } from "@/components/DiscoveryDashboard";
import { FinalPacket } from "@/components/FinalPacket";
import { Grant } from "@shared/schema";
import { StagePill } from "@/components/StagePill";

type Stage = "intake" | "discovery" | "packet";

export default function Home() {
  const [stage, setStage] = useState<Stage>("intake");
  const [profile, setProfile] = useState<IntakeProfile | null>(null);
  const [selectedGrant, setSelectedGrant] = useState<Grant | null>(null);

  const stageLabel = useMemo(() => {
    if (stage === "intake") return "Intake";
    if (stage === "discovery") return "Discovery";
    return "Final Packet";
  }, [stage]);

  const resetAll = () => {
    setStage("intake");
    setProfile(null);
    setSelectedGrant(null);
  };

  return (
    <div className="min-h-[calc(100vh-88px)] ff-mesh ff-grain">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="pt-5">
          <div className="flex flex-wrap items-center gap-2">
            <StagePill index={1} label="Intake" active={stage === "intake"} />
            <StagePill index={2} label="Discovery" active={stage === "discovery"} />
            <StagePill index={3} label="Packet" active={stage === "packet"} />
            <div className="ml-auto hidden md:block text-sm text-muted-foreground">
              Current stage: <span className="font-semibold">{stageLabel}</span>
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {stage === "intake" && (
          <motion.div
            key="intake"
            initial={{ opacity: 0, y: 12, filter: "blur(8px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -10, filter: "blur(8px)" }}
            transition={{ duration: 0.45, ease: [0.2, 0.9, 0.2, 1] }}
          >
            <SelectionPortal
              initial={profile ?? undefined}
              onForge={(p) => {
                setProfile(p);
                setStage("discovery");
              }}
            />
          </motion.div>
        )}

        {stage === "discovery" && profile && (
          <motion.div
            key="discovery"
            initial={{ opacity: 0, y: 12, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -10, filter: "blur(10px)" }}
            transition={{ duration: 0.45, ease: [0.2, 0.9, 0.2, 1] }}
          >
            <DiscoveryDashboard
              profileSummary={profile}
              selectedGrantId={selectedGrant?.id ?? null}
              onPickGrant={(g) => {
                setSelectedGrant(g);
                setStage("packet");
              }}
            />
          </motion.div>
        )}

        {stage === "packet" && profile && selectedGrant && (
          <motion.div
            key="packet"
            initial={{ opacity: 0, y: 12, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -10, filter: "blur(10px)" }}
            transition={{ duration: 0.45, ease: [0.2, 0.9, 0.2, 1] }}
          >
            <FinalPacket
              grant={selectedGrant}
              profile={profile}
              onBack={() => setStage("discovery")}
              onReset={resetAll}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Safety: if state is inconsistent, reset */}
      {stage !== "intake" && !profile && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
          <button
            onClick={resetAll}
            className="rounded-xl border border-border/60 bg-card/35 px-4 py-3 text-sm backdrop-blur hover:brightness-[1.03] transition"
          >
            State mismatch — return to intake
          </button>
        </div>
      )}
    </div>
  );
}
