## Packages
(none needed)

## Notes
- Static logo asset: import from `@assets/FundingForge_Logo_1772196329334.png`
- SSE stream: GET `/api/forge/:grantId` returns Server-Sent Events lines like `data: {"step": "...", "done": false}`; stop when `done: true`
- API routes available: GET `/api/grants`, GET `/api/faculty`
- No CRUD endpoints exist for grants/faculty; UI is read-only for these resources (backend seeds data)
