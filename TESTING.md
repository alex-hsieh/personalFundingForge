# Testing Guide

This document provides a comprehensive overview of the testing strategy for the FundingForge application.

## Test Structure

```
├── server/__tests__/          # Server-side unit/integration tests
│   ├── routes.test.ts         # API endpoint tests
│   ├── storage.test.ts        # Database layer tests
│   └── agent-client.test.ts   # Agent service integration tests
│
├── e2e/                       # End-to-end tests
│   ├── full-flow.spec.ts      # Complete user journey tests
│   ├── api-integration.spec.ts # Frontend-backend integration
│   └── forge-stream.spec.ts   # SSE streaming tests
│
├── playwright.config.ts       # E2E test configuration
└── playwright.server.config.ts # Server test configuration
```

## Quick Start

### Run server tests (no dev server needed)
```bash
npm test
```

### Run E2E tests (auto-starts dev server)
```bash
npm run test:e2e
```

### Run all tests
```bash
npm run test:all
```

### Run tests with UI
```bash
npm run test:ui          # Server tests
npm run test:e2e:ui      # E2E tests
```

## Important Notes

- **Server tests** (`npm test`) don't require the dev server - they start their own test server
- **E2E tests** (`npm run test:e2e`) automatically start the dev server before running
- If E2E tests fail to start, ensure your `.env` file has `DATABASE_URL` set
- You can also manually start the dev server (`npm run dev`) and run E2E tests separately

## Test Types

### 1. Server-Side Tests (`server/__tests__/`)

**Purpose**: Test backend logic in isolation

**What they test**:
- API endpoints (GET /api/grants, GET /api/faculty, GET /api/forge/:id)
- Database operations (CRUD for grants and faculty)
- Agent service integration
- Error handling and edge cases

**How to run**:
```bash
npm test
```

**Key features**:
- Run sequentially to avoid database conflicts
- Mock agent service when unavailable
- Test both success and error scenarios

### 2. End-to-End Tests (`e2e/`)

**Purpose**: Test the complete application flow from user perspective

**What they test**:
- Full user journey (intake → discovery → forge)
- Frontend-backend integration
- Real browser interactions
- SSE streaming
- Error states and recovery

**How to run**:
```bash
npm run test:e2e
```

**Key features**:
- Automatically starts dev server
- Tests in real browsers (Chrome, Firefox, Safari)
- Captures screenshots and traces on failure
- Supports parallel execution

## Test Scenarios

### Server Tests

#### Routes Tests
- ✅ GET /api/grants returns grant list
- ✅ GET /api/faculty returns faculty list
- ✅ GET /api/forge/:id streams SSE events
- ✅ Invalid grant ID returns 404

#### Storage Tests
- ✅ Create and retrieve grants
- ✅ Create and retrieve faculty
- ✅ Handle non-existent records
- ✅ Validate data structure

#### Agent Client Tests
- ✅ Handle service unavailable
- ✅ Stream JSON lines when available
- ✅ Parse SSE events correctly

### E2E Tests

#### Full Flow Tests
- ✅ Complete intake form
- ✅ Navigate to discovery dashboard
- ✅ Search and filter grants
- ✅ Select grant and trigger forge
- ✅ View forge results
- ✅ Navigate back through stages

#### API Integration Tests
- ✅ Fetch grants from API
- ✅ Fetch faculty from API
- ✅ Stream forge events via SSE
- ✅ Handle API errors gracefully
- ✅ Retry failed requests

#### Forge Stream Tests
- ✅ Stream progress events
- ✅ Display final results
- ✅ Handle mock fallback
- ✅ Show collaborator recommendations
- ✅ Display compliance checklist
- ✅ Show proposal draft

## Configuration

### Server Tests (`playwright.server.config.ts`)
```typescript
{
  testDir: './server/__tests__',
  fullyParallel: false,  // Sequential execution
  workers: 1,            // Single worker
  timeout: 30000         // 30 second timeout
}
```

### E2E Tests (`playwright.config.ts`)
```typescript
{
  testDir: './e2e',
  fullyParallel: true,   // Parallel execution
  baseURL: 'http://localhost:5000',
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5000',
    reuseExistingServer: true
  }
}
```

## Prerequisites

### Required
- Node.js and npm installed
- DATABASE_URL environment variable set
- PostgreSQL database running

### Optional
- Python agent service running at http://localhost:8001 (for real agent integration)
- Otherwise, tests use mock fallback

## Environment Setup

Create a `.env` file with:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/fundingforge
AGENT_SERVICE_URL=http://localhost:8001  # Optional
```

## Running Tests in CI/CD

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    npm install
    npm run db:push
    npm run test:all
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    CI: true
```

## Debugging Tests

### View test report
```bash
npx playwright show-report
```

### Run specific test
```bash
npx playwright test e2e/full-flow.spec.ts
```

### Debug mode
```bash
npx playwright test --debug
```

### Headed mode (see browser)
```bash
npx playwright test --headed
```

### Slow motion
```bash
npx playwright test --headed --slow-mo=1000
```

## Best Practices

### Writing Tests
1. Use descriptive test names
2. Test one thing per test
3. Clean up after tests
4. Use proper assertions
5. Handle async operations correctly

### Test Organization
1. Group related tests with `describe`
2. Use `beforeEach` for setup
3. Use `afterEach` for cleanup
4. Keep tests independent

### Error Handling
1. Test both success and failure cases
2. Mock external dependencies when needed
3. Use proper timeouts
4. Provide helpful error messages

## Common Issues

### Port already in use
```bash
# Kill process on port 5000
npx kill-port 5000
```

### Database connection errors
```bash
# Check DATABASE_URL is set
echo $DATABASE_URL

# Push database schema
npm run db:push
```

### Tests timing out
```typescript
// Increase timeout in test file
test.setTimeout(120000); // 2 minutes
```

### Agent service unavailable
Tests automatically fall back to mock data when the agent service is unavailable. This is expected behavior.

## Coverage

To generate coverage reports (requires additional setup):
```bash
npm install --save-dev @playwright/test-coverage
npx playwright test --coverage
```

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Tests](https://playwright.dev/docs/debug)
- [CI/CD Integration](https://playwright.dev/docs/ci)
