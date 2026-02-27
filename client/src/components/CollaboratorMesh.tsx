import { Faculty } from "@shared/schema";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mail, Users, Info, X } from "lucide-react";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts.slice(0, 2).map((p) => p[0]?.toUpperCase()).join("");
}

export function CollaboratorMesh({
  faculty,
  onPing,
}: {
  faculty: Faculty[];
  onPing: (person: Faculty) => void;
}) {
  const [selectedFac, setSelectedFac] = useState<Faculty | null>(null);

  return (
    <Card className="ff-grain rounded-2xl border border-border/60 bg-card/35 p-5 backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-accent" />
            <div className="text-sm font-semibold">Collaborator Mesh</div>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Suggested collaborators aligned to match criteria (seeded list). Click for details.
          </p>
        </div>
        <Badge variant="secondary" className="border border-border/60">
          {faculty.length} profiles
        </Badge>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {faculty.slice(0, 3).map((f) => (
          <div
            key={f.id}
            className="group flex flex-col gap-3 rounded-xl border border-border/60 bg-background/20 p-3 sm:flex-row sm:items-center sm:justify-between cursor-pointer hover:bg-background/30 transition-colors"
            onClick={() => setSelectedFac(f)}
          >
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarImage src={f.imageUrl} alt={f.name} />
                <AvatarFallback>{initials(f.name)}</AvatarFallback>
              </Avatar>
              <div>
                <div className="text-sm font-semibold group-hover:text-primary transition-colors">{f.name}</div>
                <div className="text-xs text-muted-foreground">
                  {f.department} · {f.expertise}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFac(f);
                }}
              >
                <Info className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="border border-border/60"
                onClick={(e) => {
                  e.stopPropagation();
                  onPing(f);
                }}
              >
                <Mail className="mr-2 h-4 w-4" />
                Ping
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={!!selectedFac} onOpenChange={() => setSelectedFac(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{selectedFac?.name}</DialogTitle>
            <DialogDescription>
              {selectedFac?.department} · {selectedFac?.expertise}
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col items-center gap-4 py-4">
            <Avatar className="h-24 w-24">
              <AvatarImage src={selectedFac?.imageUrl} alt={selectedFac?.name} />
              <AvatarFallback>{selectedFac ? initials(selectedFac.name) : ""}</AvatarFallback>
            </Avatar>
            <div className="text-center">
              <h4 className="font-semibold mb-2">Research Biography</h4>
              <p className="text-sm text-muted-foreground italic">
                {selectedFac?.bio || "Research biography not available for this profile in prototype."}
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
