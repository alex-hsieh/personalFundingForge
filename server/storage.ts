import { db } from "./db";
import { grants, faculty, type Grant, type InsertGrant, type Faculty, type InsertFaculty } from "@shared/schema";
import { eq } from "drizzle-orm";

export interface IStorage {
  getGrants(): Promise<Grant[]>;
  getGrantById(id: number): Promise<Grant | undefined>;
  createGrant(grant: InsertGrant): Promise<Grant>;
  getFaculty(): Promise<Faculty[]>;
  createFaculty(faculty: InsertFaculty): Promise<Faculty>;
}

export class DatabaseStorage implements IStorage {
  async getGrants(): Promise<Grant[]> {
    return await db.select().from(grants);
  }
  async getGrantById(id: number): Promise<Grant | undefined> {
    const [grant] = await db.select().from(grants).where(eq(grants.id, id));
    return grant;
  }
  async createGrant(grant: InsertGrant): Promise<Grant> {
    const [created] = await db.insert(grants).values(grant).returning();
    return created;
  }
  async getFaculty(): Promise<Faculty[]> {
    return await db.select().from(faculty);
  }
  async createFaculty(fac: InsertFaculty): Promise<Faculty> {
    const [created] = await db.insert(faculty).values(fac).returning();
    return created;
  }
}

export const storage = new DatabaseStorage();
