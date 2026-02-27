import { useEffect, useMemo, useRef, useState } from "react";
import { buildUrl, streams } from "@shared/routes";
import { z } from "zod";

export type ForgeEvent = z.infer<typeof streams.forge.chunk>;

function parseSseLine(rawLine: string): unknown | null {
  // Expect "data: {json}"
  const line = rawLine.trim();
  if (!line.startsWith("data:")) return null;
  const payload = line.slice(5).trim();
  if (!payload) return null;
  try {
    return JSON.parse(payload);
  } catch (e) {
    console.error("[SSE] Failed JSON.parse:", payload, e);
    return null;
  }
}

export function useForgeStream(grantId: number | null, enabled: boolean) {
  const [events, setEvents] = useState<ForgeEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const url = useMemo(() => {
    if (!grantId) return null;
    return buildUrl(streams.forge.path, { grantId });
  }, [grantId]);

  useEffect(() => {
    if (!enabled || !url) return;

    setEvents([]);
    setConnected(false);
    setDone(false);
    setError(null);

    const controller = new AbortController();
    abortRef.current = controller;

    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(url, {
          method: "GET",
          credentials: "include",
          signal: controller.signal,
          headers: {
            Accept: "text/event-stream",
          },
        });

        if (!res.ok || !res.body) {
          throw new Error(`Stream failed: ${res.status}`);
        }

        setConnected(true);

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { value, done: readerDone } = await reader.read();
          if (readerDone) break;

          buffer += decoder.decode(value, { stream: true });

          // SSE messages separated by blank line
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            const lines = part.split("\n");
            for (const line of lines) {
              const raw = parseSseLine(line);
              if (!raw) continue;

              const parsed = streams.forge.chunk.safeParse(raw);
              if (!parsed.success) {
                console.error("[SSE] Chunk validation failed:", parsed.error.format(), raw);
                continue;
              }

              const chunk = parsed.data;
              if (cancelled) return;

              setEvents((prev) => [...prev, chunk]);
              if (chunk.done) {
                setDone(true);
              }
            }
          }
        }
      } catch (e: any) {
        if (e?.name === "AbortError") return;
        console.error("[SSE] Stream error:", e);
        setError(e?.message || "Stream error");
      } finally {
        setConnected(false);
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [enabled, url]);

  const cancel = () => abortRef.current?.abort();

  return { events, connected, done, error, cancel };
}
