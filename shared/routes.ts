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

export const streams = {
  forge: {
    path: '/api/forge/:grantId',
    chunk: z.object({ step: z.string(), done: z.boolean(), result: z.any().optional() })
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