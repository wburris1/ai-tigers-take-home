# Wilder's Submission

## Setup Instructions

## Infrastructure
**Stack**
I built the frontend using React for the UI to create clean and simple components and state management, and used Vite for fast and easy bundling/startup. I wrote the core frontend logic in TypeScript to guarantee type safety. I used TanStack React Query hooks to make asynchronous requests to the backend because it handles caching automatically, and makes error handling, refetching, and more much simpler.
For the backend, I used Python given its extensive access to libraries and ease of use, especially for making requests to GenAI APIs. I set up a REST API with FastAPI due to its speed and simplification of the development process. For simple token encoding/decoding I used the PyJWT library. I used the `google-genai` library to make requests to the Gemini API as instructed by Google's Gemini API Quickstart guide. For handling SQL queries I used the `sqlite3` library.

**Authentication**
For the authentication flow, the client posts credentials to `POST /api/login`. On success the API returns a JWT signed with `JWT_SECRET`. The SPA stores the token (e.g. `localStorage`) and sends `Authorization: Bearer <token>` on protected calls. `GET /api/data` and `POST /api/ai-request` depend on `get_current_user`, which validates the JWT; invalid or missing tokens yield `401` error.

**AI Pipeline**
The client sends the user’s natural language question to `POST /api/ai-request`. The server:

1. Loads schema only from the SQLite file (table names and columns via `PRAGMA table_info`).
2. Calls Gemini with structured JSON output (`{ "sql": "..." }`) so the model returns a single SQLite `SELECT` (or `WITH ... SELECT`).
3. Validates the SQL programmatically (read-only `SELECT` / `WITH`, forbidden keywords, no `sqlite_*` system tables, no semicolons for multi-statements).
4. Executes the query against the same `.db` file using a read-only SQLite URI and caps rows.
5. Calls Gemini again with a compact JSON payload of columns, rows, and a truncation flag, and asks for a concise natural-language answer grounded only in that result.

The HTTP response includes the final answer text, the model id, the generated SQL (for transparency), and an optional `result_preview` for debugging.

## Scale & Production Design
**Architectural Improvements**
- To make this web app actually reach users I'd have to serve the frontend with a CDN like Cloudflare or Amazon Cloudfront and host it statically with a platform like Vercel (and integrate Next.js for faster deploys).
- I would run my API with multiple containers using Docker and manage traffic through a load balancer to ensure it is evenly distributed across containers (using Kubernetes seems like overkill for moderate traffic). I'd deploy the Dockerized API through a cloud provider like AWS or GCP and update my frontend to make requests to the deployed API.
- Regarding the data, I would migrate to a managed relational database like Postgres and update my API to target the new database (SQLite runs inside the app which will break at scale).
- For Gemini requests I'd implement usage quotas, rate limiting (will expand in next section), and cap payload size to ensure usage quotas aren't abused, as well as timeouts and retries to improve UX. I may also add Redis caching for duplicate prompts and small SQL query results. 
- I'd create separate environments for dev/staging/prod to keep testing isolated.

**Security**
- To improve token management at scale, I'd add refresh tokens and rotation: use a JWT access token with a short expiration and then a refresh token stored in the database securely which refreshes on each request to ensure users cannot steal tokens.
- I would improve storing secrets by using a secrets manager provided by AWS or Google so secrets don't live in the codebase and config can easily be changed without redeploying.
- For rate limiting, I would store request counts for each endpoint per user ID or IP address with Redis on the network edge using an Edge provider like Cloudflare or AWS and implement sliding time windows, then only allow requests when the request count within the window is below the cap (e.g. 100 requests per minute). To improve this for Gemini requests, because they are expensive and in this case my backend is the client, I would add a global limiter for requests to that endpoint and potentially even use a queue to process requests at a controlled rate.
- Other ways I would handle security include input validation using ORM parametrized queries to protect against SQL injection, identifying suspicious users by tracking failed logins and spikes in requests with something like Sentry, enforce strong passwords, and only allow requests from trusted origins.

**Monitoring**
- For tracking general app metrics I would use Prometheus to track performance like latency, query times, etc..., usage metrics like user counts and request counts, request failures and exceptions, and system health like CPU, memory, network, and disk usage.
- I would improve logging with Sentry for any meaningful events in the backend and log more extensive data like timestamps, error stack traces, and anything else that may be relevant.
- I would add healthchecks to every endpoint which ping periodically and integrate with a load balancer to remove failing instances.
- Given all this logging, I would use a dashboard like Datadog to visualize it and add alerts when a metric goes into a danger zone.