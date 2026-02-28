import { z } from 'zod';
import { grants, faculty } from './schema';

export const api = {
  grants: {
    list: {
      method: 'GET' as const,
      path: '/api/grants' as const,
      responses: {
        200: z.array(z.custom<typeof grants.$inferSelect>()),
      }
    }
  },
  faculty: {
    list: {
      method: 'GET' as const,
      path: '/api/faculty' as const,
      responses: {
        200: z.array(z.custom<typeof faculty.$inferSelect>()),
      }
    }
  }
};

export const forgeStreamChunkSchema = z.object({
  step: z.string(),
  done: z.boolean(),
  error: z.boolean().optional(),
  result: z.object({
    proposalDraft: z.string(),
    collaborators: z.array(z.object({
      name: z.string(),
      department: z.string(),
      expertise: z.string(),
      relevanceScore: z.number()
    })),
    matchScore: z.number().min(0).max(100),
    matchJustification: z.string(),
    complianceChecklist: z.array(z.object({
      task: z.string(),
      category: z.enum(["RAMP", "COI", "IRB", "Policy"]),
      status: z.enum(["green", "yellow", "red"])
    }))
  }).optional()
});

export type ForgeStreamChunk = z.infer<typeof forgeStreamChunkSchema>;

export const streams = {
  forge: {
    path: '/api/forge/:grantId',
    chunk: forgeStreamChunkSchema
  }
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}