import { useLocation } from "wouter";
import { BrandMark } from "@/components/BrandMark";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Moon, Sun, RotateCcw, ShieldCheck } from "lucide-react";
import { useMemo } from "react";

function getIsDark() {
  return typeof document !== "undefined" ? document.documentElement.classList.contains("dark") : true;
}

export function GlassTopNav({
  stageLabel,
  onReset,
}: {
  stageLabel: string;
  onReset: () => void;
}) {
  const [, setLocation] = useLocation();

  const isDark = useMemo(() => getIsDark(), []);

  const toggleTheme = () => {
    const root = document.documentElement;
    root.classList.toggle("dark");
  };

  return (
    <header className="sticky top-0 z-[999]">
      <div className="ff-grain ff-mesh border-b border-border/70">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="ff-glass my-4 rounded-2xl px-4 py-3">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center justify-between gap-3">
                <button
                  onClick={() => setLocation("/")}
                  className="rounded-xl outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2"
                  aria-label="Go to home"
                >
                  <BrandMark />
                </button>

                <div className="flex items-center gap-2 md:hidden">
                  <Button size="icon" variant="ghost" onClick={toggleTheme} aria-label="Toggle theme">
                    {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                  </Button>
                  <Button size="icon" variant="ghost" onClick={onReset} aria-label="Reset flow">
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span className="font-medium">RAMP-aware</span>
                </Badge>
                <span className="hidden md:block text-sm text-muted-foreground">
                  {stageLabel}
                </span>
                <Separator orientation="vertical" className="hidden h-6 md:block" />
                <Badge className="bg-accent text-accent-foreground border border-accent/30">
                  {stageLabel}
                </Badge>
              </div>

              <div className="hidden md:flex items-center gap-2">
                <Button
                  variant="secondary"
                  onClick={onReset}
                  className="border border-border/60"
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Reset
                </Button>
                <Button size="icon" variant="ghost" onClick={toggleTheme} aria-label="Toggle theme">
                  {getIsDark() ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="mt-3 ff-spear-divider opacity-70" />
          </div>
        </div>
      </div>
    </header>
  );
}
