import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sparkles, ChevronRight, GraduationCap, School, UserCog } from "lucide-react";
import { cn } from "@/lib/utils";

export type IntakeProfile = {
  role: "Faculty" | "Grad Student" | "Undergrad";
  year: string;
  program: string;
  cv?: File;
};

const roleCards = [
  {
    role: "Faculty" as const,
    title: "Faculty",
    icon: UserCog,
    blurb: "Pre-award routing, collaborators, and internal timelines — curated.",
  },
  {
    role: "Grad Student" as const,
    title: "Grad Student",
    icon: GraduationCap,
    blurb: "Fellowship targeting plus narrative scaffolding built for PhD and MSc students.",
  },
  {
    role: "Undergrad" as const,
    title: "Undergraduate",
    icon: School,
    blurb: "Fast discovery, mentorship alignment, and compliance guidance — simplified.",
  },
];

export function SelectionPortal({
  initial,
  onForge,
}: {
  initial?: IntakeProfile;
  onForge: (profile: IntakeProfile) => void;
}) {
  const [role, setRole] = useState<IntakeProfile["role"]>(initial?.role ?? "Faculty");
  const [year, setYear] = useState(initial?.year ?? "Year 1");
  const [program, setProgram] = useState(initial?.program ?? "Computer Science");
  const [cv, setCv] = useState<File | null>(null);

  const years = useMemo(() => {
    if (role === "Undergrad") return ["Freshman", "Sophomore", "Junior", "Senior"];
    if (role === "Grad Student") return ["MSc Year 1", "MSc Year 2", "PhD Year 1", "PhD Year 2", "PhD Year 3", "PhD Year 4+", "ABD"];
    return ["Pre-tenure", "Tenure-track", "Tenured", "Research faculty"];
  }, [role]);

  const programs = useMemo(
    () => [
      "Computer Science",
      "Engineering",
      "Psychology",
      "Biology",
      "Economics",
      "Information",
      "Education",
      "Interdisciplinary Studies",
    ],
    [],
  );

  const canForge = Boolean(role && year && program);

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
      <motion.div
        className="ff-animate-in"
        initial={{ opacity: 0, y: 10, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.55, ease: [0.2, 0.9, 0.2, 1] }}
      >
        <div className="pt-10 md:pt-14">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/40 px-3 py-1 text-xs text-muted-foreground backdrop-blur">
                <Sparkles className="h-3.5 w-3.5 text-accent" />
                Selection Portal · 3-click flow
              </div>

              <h1 className="mt-4 text-3xl sm:text-4xl md:text-5xl">
                Forge a grant-ready profile — then let the system do the heavy lifting.
              </h1>

              <p className="mt-4 max-w-2xl text-base text-muted-foreground md:text-lg">
                FundingForge turns a quick intake into a curated discovery dashboard and a polished,
                compliance-aware packet — with an agentic stream that shows its work.
              </p>

              <div className="mt-7 grid gap-3 sm:grid-cols-3">
                {roleCards.map((c) => {
                  const Icon = c.icon;
                  const active = role === c.role;
                  return (
                    <button
                      key={c.role}
                      onClick={() => setRole(c.role)}
                      className={cn(
                        "ff-grain rounded-2xl border border-border/60 bg-card/35 p-4 text-left backdrop-blur transition-transform duration-300",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                        active ? "ff-glow" : "",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className={cn("rounded-xl p-2 ring-1 ring-border/70", active ? "bg-accent/15" : "bg-muted/40")}>
                            <Icon className={cn("h-5 w-5", active ? "text-accent" : "text-muted-foreground")} />
                          </div>
                          <div className="font-semibold">{c.title}</div>
                        </div>
                        <div className={cn("h-2 w-2 rounded-full", active ? "bg-accent" : "bg-border")} />
                      </div>
                      <p className="mt-3 text-sm text-muted-foreground">{c.blurb}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            <Card className="ff-grain border border-border/60 bg-card/40 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-xl">Intake</CardTitle>
                <p className="text-sm text-muted-foreground">
                  A few structured choices unlock tailored discovery + packet scaffolding.
                </p>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select value={role} onValueChange={(v) => setRole(v as IntakeProfile["role"])}>
                    <SelectTrigger className="bg-background/40">
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Faculty">Faculty</SelectItem>
                      <SelectItem value="Grad Student">Grad Student</SelectItem>
                      <SelectItem value="Undergrad">Undergrad</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Year / Level</Label>
                  <Select value={year} onValueChange={setYear}>
                    <SelectTrigger className="bg-background/40">
                      <SelectValue placeholder="Select year" />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map((y) => (
                        <SelectItem key={y} value={y}>
                          {y}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Program</Label>
                  <Select value={program} onValueChange={setProgram}>
                    <SelectTrigger className="bg-background/40">
                      <SelectValue placeholder="Select program" />
                    </SelectTrigger>
                    <SelectContent>
                      {programs.map((p) => (
                        <SelectItem key={p} value={p}>
                          {p}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cv-upload">Upload CV (Optional)</Label>
                  <div className="flex items-center gap-2">
                    <input
                      id="cv-upload"
                      type="file"
                      className="hidden"
                      onChange={(e) => setCv(e.target.files?.[0] || null)}
                      accept=".pdf,.doc,.docx"
                    />
                    <Button
                      variant="outline"
                      className="w-full bg-background/40"
                      onClick={() => document.getElementById("cv-upload")?.click()}
                    >
                      {cv ? cv.name : "Choose file"}
                    </Button>
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    onClick={() => onForge({ role, year, program, cv: cv || undefined })}
                    disabled={!canForge}
                    className={cn(
                      "w-full border border-accent/30 bg-accent text-accent-foreground",
                      "shadow-lg shadow-accent/20",
                    )}
                  >
                    Forge My Profile
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                  <p className="mt-3 text-xs text-muted-foreground">
                    This MVP uses seeded grant + faculty data and a simulated forging stream.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-10 ff-spear-divider opacity-60" />

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {[
              { k: "Discovery", v: "Grants matched to your profile shape + keywords." },
              { k: "Compliance", v: "Internal deadlines + RAMP checklist preflight." },
              { k: "Packet", v: "Draft narrative + collaborator mesh + task toggles." },
            ].map((x) => (
              <div
                key={x.k}
                className="rounded-2xl border border-border/60 bg-card/30 p-4 backdrop-blur"
              >
                <div className="text-sm font-semibold">{x.k}</div>
                <div className="mt-1 text-sm text-muted-foreground">{x.v}</div>
              </div>
            ))}
          </div>

          <div className="pb-10 md:pb-14" />
        </div>
      </motion.div>
    </div>
  );
}
