import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Copy, Download } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function ProposalDraft({
  grantName,
  profile,
  done,
}: {
  grantName: string;
  profile: { role: string; year: string; program: string };
  done: boolean;
}) {
  const { toast } = useToast();
  const initial = useMemo(() => {
    return `Title: ${grantName} — Detailed Research Strategy & Narrative Scaffold

1. Executive Summary
This comprehensive proposal draft for the ${grantName} program serves as a high-signal foundation for ${profile.role} applicants within the ${profile.program} department. Based on current profile metrics (${profile.year}), this scaffold highlights critical alignment with FSU's research mission and sponsor-specific intellectual merit.

2. Problem Statement & Research Significance
The proposed research addresses fundamental gaps in ${profile.program} by investigating complex interactions between theoretical models and real-world datasets. This work is significant because it directly supports FSU's commitment to innovation and interdisciplinary inquiry.

3. Intellectual Merit
The investigation leverages cutting-edge methodology and rigorous experimental design. We propose a crisp, testable agenda with clearly defined milestones, risk assessment, and robust contingency paths to ensure successful project completion.

4. Broader Impacts
Beyond technical advancement, this project will foster professional development for ${profile.role}s and integrate diverse educational outreach. Dissemination plans include open-access publication and presentations at premier ${profile.program} symposia.

5. Training & Mentorship Plan
Aligned with ${profile.year} status, the plan emphasizes mastery of technical skills, grant writing proficiency, and leadership in research group dynamics.

6. Institutional Context: Why FSU?
Florida State University provides a unique environment for this work, offering state-of-the-art facilities and a collaborative faculty network through the FundingForge Collaborator Mesh.

Word Count Requirement Tracker:
- Current Draft: ~350 words
- Target Requirement: 1,500 words (approx. 23% complete)
- Recommendation: Expand Section 2 with 3 specific case studies and Section 3 with detailed technical implementation phases.
`;
  }, [grantName, profile.program, profile.role, profile.year]);

  const [text, setText] = useState(initial);

  const wordCount = useMemo(() => {
    return text.trim().split(/\s+/).length;
  }, [text]);

  const progress = Math.min(Math.round((wordCount / 1500) * 100), 100);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(text);
      toast({ title: "Copied", description: "Proposal draft copied to clipboard." });
    } catch {
      toast({ title: "Copy failed", description: "Clipboard permission blocked.", variant: "destructive" });
    }
  };

  const downloadTxt = () => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `FundingForge_${grantName.replace(/\s+/g, "_")}_draft.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast({ title: "Downloaded", description: "Draft saved as .txt." });
  };

  return (
    <Card className="ff-grain rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-accent" />
            <div className="text-sm font-semibold">Proposal Draft</div>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Editable scaffold — export or copy into your internal workflow.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary" className="border border-border/60">
            {done ? "Forged" : "Drafting…"}
          </Badge>
          <div className="flex flex-col items-end gap-1">
            <div className="text-[10px] font-medium text-muted-foreground">
              {wordCount} / 1500 words
            </div>
            <div className="h-1 w-24 rounded-full bg-secondary overflow-hidden">
              <div 
                className="h-full bg-accent transition-all duration-500" 
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
          <Button variant="secondary" className="border border-border/60" onClick={copyToClipboard}>
            <Copy className="mr-2 h-4 w-4" />
            Copy
          </Button>
          <Button onClick={downloadTxt} className="bg-accent text-accent-foreground border border-accent/30">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      <div className="mt-4">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="min-h-[260px] bg-background/30"
          placeholder="Draft will appear here…"
        />
      </div>
    </Card>
  );
}
