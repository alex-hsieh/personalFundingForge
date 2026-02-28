# End-to-End Tests

This directory contains end-to-end tests that validate the full application flow, testing both frontend and backend together.

## Test Structure

- `full-flow.spec.ts` - Complete user journey from intake to forge completion
- `api-integration.spec.ts` - Frontend-backend API integration tests
- `forge-stream.spec.ts` - Server-Sent Events (SSE) streaming tests

## Running Tests

### Run all E2E tests (starts dev server automatically)
```bash
npm run test:e2e
```

### Run E2E tests with UI
```bash
npm run test:e2e:ui
```

### Run all tests (server + E2E)
```bash
npm run test:all
```

### Run specific test file
```bash
npx playwright test e2e/full-flow.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test e2e --headed
```

### Debug tests
```bash
npx playwright test e2e --debug
```

## Prerequisites

1. **Database**: Ensure DATABASE_URL is set in your .env file
2. **Dev Server**: Tests automatically start the dev server on port 5000
3. **Agent Service** (optional): For real agent integration, run the Python service at http://localhost:8001

## Test Coverage

### Full Flow Tests
- Complete intake → discovery → forge workflow
- Grant search and filtering
- Faculty list display
- Back navigation
- Error handling

### API Integration Tests
- Grants API endpoint validation
- Faculty API endpoint validation
- SSE forge stream connection
- API error handling
- Retry logic

### Forge Stream Tests
- Progress event streaming
- Final result display
- Mock fallback behavior
- Stream error handling
- Collaborator recommendations
- Compliance checklist display
- Proposal draft display

## Configuration

The E2E tests use the main `playwright.config.ts` which:
- Runs tests against `http://localhost:5000`
- Automatically starts dev server before tests
- Reuses existing server in development
- Runs tests in parallel (configurable)
- Supports multiple browsers (chromium, firefox, webkit)

## Notes

- Tests automatically start and stop the dev server
- The dev server timeout is set to 120 seconds to allow for database initialization
- Tests use mock data when the agent service is unavailable
- All tests include proper cleanup and error handling
- Tests are designed to be idempotent and can run in any order

## Debugging Tips

1. **View test report**: After running tests, open `playwright-report/index.html`
2. **Use UI mode**: Run `npm run test:e2e:ui` for interactive debugging
3. **Check traces**: Failed tests automatically capture traces in the report
4. **Slow down tests**: Add `page.waitForTimeout(1000)` to see what's happening
5. **Use headed mode**: Run with `--headed` flag to see the browser

## Common Issues

### Port already in use
If port 5000 is already in use, stop the existing process or change the port in:
- `playwright.config.ts` (baseURL and webServer.url)
- `server/index.ts` (default port)

### Database connection errors
Ensure your DATABASE_URL is set correctly in `.env` file

### Tests timing out
Increase timeout in test file: `test.setTimeout(120000)` for 2 minutes
