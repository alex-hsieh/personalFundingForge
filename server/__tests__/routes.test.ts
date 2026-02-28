import { describe, it, expect, beforeAll, afterAll } from '@playwright/test';
import type { Express } from 'express';
import express from 'express';
import { registerRoutes } from '../routes';
import { createServer, type Server } from 'http';

describe('Server Routes', () => {
  let app: Express;
  let httpServer: Server;
  let baseURL: string;

  beforeAll(async () => {
    // Setup test server
    app = express();
    app.use(express.json());
    httpServer = createServer(app);
    
    await registerRoutes(httpServer, app);
    
    // Start server on random port
    await new Promise<void>((resolve) => {
      httpServer.listen(0, () => {
        const address = httpServer.address();
        const port = typeof address === 'object' && address ? address.port : 5000;
        baseURL = `http://localhost:${port}`;
        resolve();
      });
    });
  });

  afterAll(async () => {
    await new Promise<void>((resolve, reject) => {
      httpServer.close((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  });

  describe('GET /api/grants', () => {
    it('should return list of grants', async () => {
      const response = await fetch(`${baseURL}/api/grants`);
      expect(response.status).toBe(200);
      
      const grants = await response.json();
      expect(Array.isArray(grants)).toBe(true);
      
      if (grants.length > 0) {
        expect(grants[0]).toHaveProperty('name');
        expect(grants[0]).toHaveProperty('targetAudience');
      }
    });
  });

  describe('GET /api/faculty', () => {
    it('should return list of faculty', async () => {
      const response = await fetch(`${baseURL}/api/faculty`);
      expect(response.status).toBe(200);
      
      const faculty = await response.json();
      expect(Array.isArray(faculty)).toBe(true);
      
      if (faculty.length > 0) {
        expect(faculty[0]).toHaveProperty('name');
        expect(faculty[0]).toHaveProperty('department');
        expect(faculty[0]).toHaveProperty('expertise');
      }
    });
  });

  describe('GET /api/forge/:grantId', () => {
    it('should stream forge results', async () => {
      // First get a grant ID
      const grantsResponse = await fetch(`${baseURL}/api/grants`);
      const grants = await grantsResponse.json();
      
      if (grants.length === 0) {
        console.log('No grants available for testing');
        return;
      }

      const grantId = grants[0].id;
      const response = await fetch(
        `${baseURL}/api/forge/${grantId}?role=Faculty&year=2024&program=CS`
      );
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toBe('text/event-stream');
      
      // Read SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let receivedData = false;
      let finalResult = null;

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              receivedData = true;
              const data = JSON.parse(line.slice(6));
              
              expect(data).toHaveProperty('step');
              expect(data).toHaveProperty('done');
              
              if (data.done) {
                finalResult = data;
                break;
              }
            }
          }
          
          if (finalResult) break;
        }
      }
      
      expect(receivedData).toBe(true);
      expect(finalResult).not.toBeNull();
    });
  });
});
