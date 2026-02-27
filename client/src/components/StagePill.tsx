import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function StagePill({
  index,
  label,
  active,
}: {
  index: number;
  label: string;
  active: boolean;
}) {
  return (
    <Badge
      variant={active ? "default" : "secondary"}
      className={cn(
        "px-3 py-1 text-[12px] font-medium",
        active ? "bg-primary text-primary-foreground border border-primary/30" : "border border-border/60",
      )}
    >
      <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-md bg-background/10 text-[11px]">
        {index}
      </span>
      {label}
    </Badge>
  );
}
