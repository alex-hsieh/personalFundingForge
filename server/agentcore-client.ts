/**
 * AWS AgentCore Integration Client
 * 
 * Manages agent lifecycle and communication between Express backend and agent service.
 * Streams JSON_Line responses from the agent service.
 */

// TODO: Implement AgentCore integration
// Note: This is a placeholder implementation until AWS AgentCore SDK is available
// For now, we'll use direct HTTP calls as a fallback

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
 * Invokes the agent pipeline through AgentCore (or direct HTTP as fallback)
 * 
 * @param payload - The complete request payload for the agent service
 * @returns AsyncGenerator yielding JSON_Line responses
 */
export async function* invokeAgentPipeline(
  payload: InvokePayload
): AsyncGenerator<JSONLine> {
  const agentServiceUrl = process.env.AGENT_SERVICE_URL || 'http://localhost:8001';
  
  try {
    // TODO: Replace with AWS AgentCore client when available
    // For now, use direct HTTP call to agent service
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
