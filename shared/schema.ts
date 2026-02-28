import { pgTable, text, serial } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const grants = pgTable("grants", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  targetAudience: text("target_audience").notNull(),
  eligibility: text("eligibility").notNull(),
  matchCriteria: text("match_criteria").notNull(),
  internalDeadline: text("internal_deadline").notNull(),
});

export const faculty = pgTable("faculty", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  department: text("department").notNull(),
  expertise: text("expertise").notNull(),
  imageUrl: text("image_url").notNull(),
  bio: text("bio").default(""),
});

export const insertGrantSchema = createInsertSchema(grants).omit({ id: true });
export const insertFacultySchema = createInsertSchema(faculty).omit({ id: true });

export type Grant = typeof grants.$inferSelect;
export type InsertGrant = z.infer<typeof insertGrantSchema>;
export type Faculty = typeof faculty.$inferSelect;
export type InsertFaculty = z.infer<typeof insertFacultySchema>;

export const buildUrl = (path: string, params?: Record<string, any>) => {
  const url = new URL(`/api${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, String(v)));
  }
  return url.toString();
};

export const streams = {
  forge: {
    path: "/forge",
    chunk: z.object({
      content: z.string().optional(),
      done: z.boolean().optional(),
      error: z.string().optional(),
    })
  }
};
