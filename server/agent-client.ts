/**
 * Agent Service Integration Client
 * 
 * Manages communication between Express backend and Python agent service.
 * Streams JSON_Line responses from the agent service.
 * 
 * Note: AWS Bedrock AgentCore is a managed runtime service for deploying agents,
 * not a client SDK. Our architecture uses direct HTTP calls to the FastAPI agent service.
 */

interface JSONLine {
  agent: string;
  step: string;
  output: any;
  done: boolean;
}

interface InvokePayload {
  grantId: number;
  grantName: string;
  matchCriteria: string;
  eligibility: string;
  userProfile: {
    role: string;
    year: string;
    program: string;
  };
  facultyList: Array<{
    name: string;
    department: string;
    expertise: string;
    imageUrl: string;
    bio: string | null;
  }>;
}

/**
 * Invokes the agent pipeline via direct HTTP to the agent service
 * 
 * @param payload - The complete request payload for the agent service
 * @returns AsyncGenerator yielding JSON_Line responses
 */
export async function* invokeAgentPipeline(
  payload: InvokePayload
): AsyncGenerator<JSONLine> {
  const agentServiceUrl = process.env.AGENT_SERVICE_URL || 'http://localhost:8001';
  
  try {
    const response = await fetch(`${agentServiceUrl}/invoke`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Agent service returned ${response.status}`);
    }

    if (!response.body) {
      throw new Error('No response body from agent service');
    }

    // Parse newline-delimited JSON stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            const jsonLine: JSONLine = JSON.parse(line);
            yield jsonLine;
          } catch (error) {
            console.error('Failed to parse JSON line:', line, error);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error invoking agent pipeline:', error);
    throw error;
  }
}
