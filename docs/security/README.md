# Security

Security principles and planned controls for the Georgian CX Platform.

**Nothing is implemented yet.** This document captures design intent for future phases.

## Authentication (planned)

- **Access token**: short-lived JWT, sent in `Authorization: Bearer` header
- **Refresh token**: long-lived, stored in HttpOnly, Secure, SameSite cookie
- No refresh tokens in localStorage or sessionStorage
- Token rotation on refresh (to be decided in ADR)

## Authorization (planned)

- Role-based access within a workspace (e.g. agent, admin)
- All API queries scoped to the authenticated user's workspace
- No cross-tenant data leakage

## Identifiers

- Public resource IDs: **UUIDs only**
- No sequential integer IDs exposed in URLs or API responses
- Internal auto-increment keys (if used) must never be public

## Secrets management

- **Never** commit secrets, API keys, or credentials to the repository
- Use `.env` files locally (gitignored)
- Production secrets via environment or secret manager (future)
- `.env.example` files document required variables without values

## Data handling

- Customer PII stored in PostgreSQL with workspace isolation
- File attachments in MinIO with access controlled by backend
- Audit logging for sensitive operations (planned)

## API security (planned)

- HTTPS only in production
- CORS restricted to known frontend origins
- Rate limiting on auth endpoints
- Input validation via Pydantic on all endpoints

## Dependencies

- Pin dependency versions
- Regular security audits (`npm audit`, `pip-audit`) when CI is introduced

## Reporting vulnerabilities

Process to be defined before any production deployment.

## Related docs

- [Architecture overview](../architecture/README.md)
- [ADR index](../decisions/README.md)
