# Server-Side Tests

This directory contains tests for the server-side logic of the application.

## Test Structure

- `routes.test.ts` - Tests for API endpoints (grants, faculty, forge)
- `storage.test.ts` - Tests for database storage operations
- `agent-client.test.ts` - Tests for agent service integration

## Running Tests

### Run all server tests
```bash
npm test
```

### Run tests with UI
```bash
npm run test:ui
```

### Run specific test file
```bash
npx playwright test server/__tests__/routes.test.ts
```

## Prerequisites

1. **Database**: Ensure DATABASE_URL is set in your .env file
2. **Agent Service** (optional): For full agent-client tests, the Python agent service should be running at http://localhost:8001

## Test Coverage

### Routes Tests
- GET /api/grants - Validates grant list retrieval
- GET /api/faculty - Validates faculty list retrieval  
- GET /api/forge/:grantId - Validates SSE streaming and forge pipeline

### Storage Tests
- Grant CRUD operations
- Faculty CRUD operations
- Error handling for non-existent records

### Agent Client Tests
- Service unavailable handling
- JSON line streaming (requires running agent service)

## Notes

- Tests run sequentially (workers: 1) to avoid database conflicts
- Agent client tests gracefully skip if the service is unavailable
- The forge endpoint test uses mock data when the agent service is down
