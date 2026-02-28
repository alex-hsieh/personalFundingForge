import { describe, it, expect, beforeEach } from '@playwright/test';
import { DatabaseStorage } from '../storage';
import type { InsertGrant, InsertFaculty } from '@shared/schema';

describe('DatabaseStorage', () => {
  let storage: DatabaseStorage;

  beforeEach(() => {
    storage = new DatabaseStorage();
  });

  describe('Grants', () => {
    it('should create and retrieve a grant', async () => {
      const newGrant: InsertGrant = {
        name: 'Test Grant',
        targetAudience: 'Test Audience',
        eligibility: 'Test Eligibility',
        matchCriteria: 'Test Criteria',
        internalDeadline: 'Test Deadline'
      };

      const created = await storage.createGrant(newGrant);
      
      expect(created).toHaveProperty('id');
      expect(created.name).toBe(newGrant.name);
      expect(created.targetAudience).toBe(newGrant.targetAudience);
    });

    it('should retrieve all grants', async () => {
      const grants = await storage.getGrants();
      
      expect(Array.isArray(grants)).toBe(true);
    });

    it('should retrieve grant by ID', async () => {
      const grants = await storage.getGrants();
      
      if (grants.length > 0) {
        const grant = await storage.getGrantById(grants[0].id);
        
        expect(grant).toBeDefined();
        expect(grant?.id).toBe(grants[0].id);
      }
    });

    it('should return undefined for non-existent grant', async () => {
      const grant = await storage.getGrantById(999999);
      
      expect(grant).toBeUndefined();
    });
  });

  describe('Faculty', () => {
    it('should create and retrieve faculty', async () => {
      const newFaculty: InsertFaculty = {
        name: 'Dr. Test',
        department: 'Test Department',
        expertise: 'Test Expertise',
        imageUrl: 'https://example.com/test.jpg',
        bio: 'Test bio'
      };

      const created = await storage.createFaculty(newFaculty);
      
      expect(created).toHaveProperty('id');
      expect(created.name).toBe(newFaculty.name);
      expect(created.department).toBe(newFaculty.department);
    });

    it('should retrieve all faculty', async () => {
      const faculty = await storage.getFaculty();
      
      expect(Array.isArray(faculty)).toBe(true);
    });
  });
});
