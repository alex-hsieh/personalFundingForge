import logoUrl from "@assets/FundingForge_Logo_1772196329334.png";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative">
        <div className="absolute -inset-2 rounded-xl bg-gradient-to-br from-accent/25 via-primary/20 to-transparent blur-md" />
        <img
          src={logoUrl}
          alt="FundingForge"
          className="relative h-8 w-8 rounded-xl ring-1 ring-border/60"
        />
      </div>
      {!compact && (
        <div className="flex items-center font-serif text-xl tracking-tight">
          <span className="text-primary">Funding</span>
          <span className="text-accent">Forge</span>
        </div>
      )}
    </div>
  );
}
