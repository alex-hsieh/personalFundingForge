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