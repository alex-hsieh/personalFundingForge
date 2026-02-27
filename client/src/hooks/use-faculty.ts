import { useQuery } from "@tanstack/react-query";
import { api } from "@shared/routes";
import { z } from "zod";

function parseWithLogging<T>(schema: z.ZodSchema<T>, data: unknown, label: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    console.error(`[Zod] ${label} validation failed:`, result.error.format());
    throw result.error;
  }
  return result.data;
}

export function useFaculty() {
  return useQuery({
    queryKey: [api.faculty.list.path],
    queryFn: async () => {
      const res = await fetch(api.faculty.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch faculty");
      const json = await res.json();
      return parseWithLogging(api.faculty.list.responses[200], json, "faculty.list");
    },
  });
}
