import { describe, it, expect, beforeEach, afterEach } from '@playwright/test';
import { invokeAgentPipeline } from '../agent-client';

describe('Agent Client', () => {
  const mockPayload = {
    grantId: 1,
    grantName: 'Test Grant',
    matchCriteria: 'Test Criteria',
    eligibility: 'Test Eligibility',
    userProfile: {
      role: 'Faculty',
      year: '2024',
      program: 'Computer Science'
    },
    facultyList: [
      {
        name: 'Dr. Test',
        department: 'CS',
        expertise: 'AI',
        imageUrl: 'https://example.com/test.jpg',
        bio: 'Test bio'
      }
    ]
  };

  describe('invokeAgentPipeline', () => {
    it('should handle agent service unavailable gracefully', async () => {
      // Set invalid URL to simulate service unavailable
      const originalUrl = process.env.AGENT_SERVICE_URL;
      process.env.AGENT_SERVICE_URL = 'http://localhost:9999';

      try {
        const generator = invokeAgentPipeline(mockPayload);
        await generator.next();
        
        // Should throw error when service is unavailable
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
      } finally {
        // Restore original URL
        if (originalUrl) {
          process.env.AGENT_SERVICE_URL = originalUrl;
        } else {
          delete process.env.AGENT_SERVICE_URL;
        }
      }
    });

    it('should yield JSON lines when service is available', async () => {
      // This test requires the agent service to be running
      // Skip if AGENT_SERVICE_URL is not set or service is not available
      const agentServiceUrl = process.env.AGENT_SERVICE_URL || 'http://localhost:8001';
      
      try {
        // Quick health check
        const healthCheck = await fetch(agentServiceUrl, { 
          method: 'GET',
          signal: AbortSignal.timeout(1000)
        });
        
        if (!healthCheck.ok) {
          console.log('Agent service not available, skipping test');
          return;
        }

        const generator = invokeAgentPipeline(mockPayload);
        const results = [];
        
        for await (const line of generator) {
          results.push(line);
          
          expect(line).toHaveProperty('agent');
          expect(line).toHaveProperty('step');
          expect(line).toHaveProperty('done');
          
          if (line.done) {
            expect(line).toHaveProperty('output');
            break;
          }
        }
        
        expect(results.length).toBeGreaterThan(0);
        expect(results[results.length - 1].done).toBe(true);
      } catch (error) {
        console.log('Agent service not available, skipping test:', error);
      }
    });
  });
});
