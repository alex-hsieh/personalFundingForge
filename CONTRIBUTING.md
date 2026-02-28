# Contributing to FundingForge

Thank you for your interest in contributing to FundingForge! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- AWS Account with Bedrock access

### Quick Setup

**Option 1: Automated Setup**
```bash
# On macOS/Linux
chmod +x setup.sh
./setup.sh

# On Windows (PowerShell)
.\setup.ps1
```

**Option 2: Manual Setup**
```bash
# Install Node.js dependencies
npm install

# Set up Python environment
cd agent-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Configure environment
cp .env.example .env
cp agent-service/.env.example agent-service/.env
# Edit .env files with your credentials

# Start PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# Initialize database
npm run db:push
```

## Project Structure

```
fundingforge/
├── agent-service/          # Python FastAPI agent service
│   ├── agents/            # Agent implementations
│   │   ├── sourcing.py
│   │   ├── matchmaking.py
│   │   ├── collaborator.py
│   │   ├── drafting.py
│   │   └── orchestrator.py
│   ├── notebooks/         # Jupyter notebooks for testing
│   ├── main.py           # FastAPI app
│   └── models.py         # Pydantic models
├── client/                # React frontend
│   └── src/
│       ├── components/   # UI components
│       ├── pages/        # Page components
│       └── hooks/        # Custom hooks
├── server/               # Express backend
│   ├── agentcore-client.ts
│   ├── routes.ts
│   └── storage.ts
├── shared/               # Shared TypeScript types
│   ├── schema.ts         # Database schema
│   └── routes.ts         # API contracts
└── tests/                # E2E tests
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards below.

### 3. Test Your Changes

```bash
# TypeScript type checking
npm run check

# Run E2E tests
npm test

# Test agent service
cd agent-service
pytest  # When tests are implemented
```

### 4. Commit Your Changes

Use conventional commit messages:

```bash
git commit -m "feat: add new agent capability"
git commit -m "fix: resolve streaming issue"
git commit -m "docs: update README"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow existing code style (ESLint will be configured)
- Use meaningful variable and function names
- Add JSDoc comments for public APIs
- Prefer `const` over `let`, avoid `var`
- Use async/await over promises when possible

**Example:**
```typescript
/**
 * Invokes the agent pipeline and streams results
 * @param payload - The request payload
 * @returns AsyncGenerator yielding JSON_Line responses
 */
export async function* invokeAgentPipeline(
  payload: InvokePayload
): AsyncGenerator<JSONLine> {
  // Implementation
}
```

### Python

- Follow PEP 8 style guide
- Use type hints for function signatures
- Add docstrings for all functions and classes
- Use meaningful variable and function names
- Prefer async/await for I/O operations

**Example:**
```python
async def orchestrate_pipeline(request: InvokeRequest) -> AsyncGenerator[JSONLine, None]:
    """
    Orchestrates the multi-agent pipeline.
    
    Args:
        request: The invoke request with grant and user data
        
    Yields:
        JSONLine objects with progress updates and final result
    """
    # Implementation
```

### React Components

- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use TypeScript for props
- Follow existing component patterns

**Example:**
```typescript
interface GrantCardProps {
  grant: Grant;
  onSelect: (grantId: number) => void;
}

export function GrantCard({ grant, onSelect }: GrantCardProps) {
  // Implementation
}
```

## Testing Guidelines

### Unit Tests

- Test individual functions and components
- Mock external dependencies
- Use descriptive test names
- Aim for high coverage of critical paths

### Property-Based Tests

- Use `fast-check` for TypeScript
- Use `hypothesis` for Python
- Test universal properties
- Run minimum 100 iterations

**Example:**
```typescript
// Feature: aws-bedrock-backend-integration, Property 31
test('forge endpoint fetches grant and faculty for any valid grantId', async () => {
  await fc.assert(
    fc.asyncProperty(fc.integer({ min: 1, max: 1000 }), async (grantId) => {
      // Test implementation
    }),
    { numRuns: 100 }
  );
});
```

### Integration Tests

- Test complete workflows
- Use test database
- Clean up after tests
- Test error scenarios

## Agent Development

### Adding a New Agent

1. Create agent file in `agent-service/agents/`
2. Import required dependencies from `strands`
3. Define system prompt
4. Implement agent logic
5. Add streaming progress updates
6. Create Jupyter notebook for testing
7. Add unit tests
8. Update orchestrator to include new agent

### Agent Template

```python
"""
NewAgent: Brief description

Model: Claude Haiku/Sonnet
Purpose: What this agent does
"""

from strands import Agent
from strands.models import BedrockModel

# Model configuration
model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# System prompt
SYSTEM_PROMPT = """
You are the NewAgent for FundingForge.
Your role is to...
"""

# Create agent
new_agent = Agent(model=model, system_prompt=SYSTEM_PROMPT)

async def run(input_data: dict) -> dict:
    """
    Runs the agent with given input.
    
    Args:
        input_data: Input data for the agent
        
    Returns:
        Agent output
    """
    # Implementation
    pass
```

## Database Changes

### Schema Modifications

1. Update `shared/schema.ts` with new tables/columns
2. Run `npm run db:push` to apply changes
3. Update TypeScript types if needed
4. Test with existing data

### Adding New Endpoints

1. Define schema in `shared/routes.ts`
2. Implement route in `server/routes.ts`
3. Add storage methods in `server/storage.ts`
4. Update frontend hooks if needed
5. Add tests

## Documentation

### Code Documentation

- Add JSDoc/docstrings for all public APIs
- Document complex algorithms
- Explain non-obvious decisions
- Keep comments up to date

### README Updates

- Update README.md for new features
- Add troubleshooting entries for common issues
- Update environment variable documentation
- Keep examples current

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] TypeScript compiles without errors
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive data in commits

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Getting Help

- Check existing documentation
- Review similar code in the project
- Ask questions in pull request comments
- Open an issue for bugs or feature requests

## Code Review Process

1. Automated checks run on PR
2. Maintainer reviews code
3. Address feedback
4. Approval and merge

## Release Process

1. Version bump in package.json
2. Update CHANGELOG.md
3. Create release tag
4. Deploy to production

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue or reach out to the maintainers.

Thank you for contributing to FundingForge! 🚀
