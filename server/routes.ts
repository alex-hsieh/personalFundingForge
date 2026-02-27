import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  app.get(api.grants.list.path, async (req, res) => {
    const allGrants = await storage.getGrants();
    res.json(allGrants);
  });

  app.get(api.faculty.list.path, async (req, res) => {
    const allFaculty = await storage.getFaculty();
    res.json(allFaculty);
  });

  app.get('/api/forge/:grantId', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const steps = [
      "Sourcing Agent is checking FSU internal policies...",
      "Analyzing applicant history and match criteria...",
      "Drafting proposal summary based on previous successful grants...",
      "Finding suitable FSU faculty collaborators...",
      "Validating RAMP checklist requirements..."
    ];

    let i = 0;
    const interval = setInterval(() => {
      if (i < steps.length) {
        res.write(`data: ${JSON.stringify({ step: steps[i], done: false })}\n\n`);
        i++;
      } else {
        res.write(`data: ${JSON.stringify({ step: "Complete", done: true })}\n\n`);
        clearInterval(interval);
        res.end();
      }
    }, 1500);

    req.on('close', () => clearInterval(interval));
  });

  // Seed DB with mock data for the prototype
  const existingGrants = await storage.getGrants();
  if (existingGrants.length === 0) {
    const grantsData = [
      { name: "NSF GRFP", targetAudience: "Grad Students", eligibility: "Year 1-2 PhD", matchCriteria: "STEM, Social Science, Research", internalDeadline: "72 hours before Oct deadline" },
      { name: "FSU IDEA Grant", targetAudience: "Undergrads", eligibility: "Soph/Junior", matchCriteria: "Innovation, Inquiry, Mentorship", internalDeadline: "72 hours before rolling deadline" },
      { name: "FSU CRC Planning", targetAudience: "Faculty", eligibility: "Tenure-Track", matchCriteria: "Interdisciplinary, Seed Funding", internalDeadline: "72 hours before Feb/Sept deadline" },
      { name: "McKnight Doctoral", targetAudience: "PhD Students", eligibility: "Year 1-3", matchCriteria: "Diversity, Retention, Research", internalDeadline: "72 hours before Jan deadline" },
      { name: "NSF CAREER", targetAudience: "Junior Faculty", eligibility: "Pre-Tenure", matchCriteria: "Integration, Education, Research", internalDeadline: "72 hours before July deadline" }
    ];
    for (const g of grantsData) await storage.createGrant(g);
  }

  const existingFaculty = await storage.getFaculty();
  if (existingFaculty.length === 0) {
    const facultyData = [
      { 
        name: "Dr. Sarah Chen", 
        department: "Computer Science", 
        expertise: "AI, Machine Learning", 
        imageUrl: "https://i.pravatar.cc/150?u=sarah",
        bio: "Dr. Chen focuses on neural architecture search and ethical AI frameworks. She has secured over $5M in NSF funding since 2018."
      },
      { 
        name: "Dr. Marcus Johnson", 
        department: "Engineering", 
        expertise: "Robotics, Control Systems", 
        imageUrl: "https://i.pravatar.cc/150?u=marcus",
        bio: "Specializing in autonomous marine robotics, Dr. Johnson leads the FSU Marine Robotics Lab with a focus on environmental monitoring."
      },
      { 
        name: "Dr. Elena Rodriguez", 
        department: "Information", 
        expertise: "Human-Computer Interaction", 
        imageUrl: "https://i.pravatar.cc/150?u=elena",
        bio: "Dr. Rodriguez researches accessibility in digital interfaces, particularly for neurodivergent populations in educational settings."
      }
    ];
    for (const f of facultyData) await storage.createFaculty(f);
  }

  return httpServer;
}
