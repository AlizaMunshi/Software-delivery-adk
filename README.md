root_agent (delivery_intake) is meant to greet, then capture_requirement with the user’s full ask and hand off to software_delivery_pipeline, which runs Solution Architect → DB Architect → Developer → QA → Deployment → synthesis. Prompts below match that flow.

First turn (short)
Use any of these so the intake agent can introduce the team and ask for the real requirement:

Hello
I need help planning a new feature end-to-end.
We’re starting a greenfield service—walk me through delivery.
I have a vague idea; I need architecture through deployment.
Second turn — sample requirements (paste as one message)
These are written to exercise components, data, APIs, NFRs, QA, and Cloud Run–style deployment.

1. Internal API + Postgres

Build an internal REST API for employee time-off requests: submit request, manager approve/deny, HR export. Stack preference Python/FastAPI, DB Cloud SQL Postgres, auth via Google OIDC for employees and managers. Need audit log of state changes, email notifications on approval, SLA p95 < 300ms for reads, RTO 4h for DB. Deploy on Cloud Run in us-central1, three envs (dev/stage/prod), secrets in Secret Manager. Compliance: PII in requests (names, emails)—call out encryption and retention.

2. Event-driven inventory

Design an inventory sync between our e-commerce monolith (MySQL) and a new read-optimized catalog service. Updates should go through Pub/Sub; catalog is document store (Firestore or MongoDB—pick and justify). Need idempotent consumers, dead-letter handling, backfill from MySQL, and event ordering strategy where it matters. NFRs: 99.9% availability for catalog reads, eventual consistency acceptable for stock display. Include CI test strategy and canary deployment on GKE or Cloud Run.

3. Batch + data pipeline

Add a nightly billing reconciliation job: pull transactions from BigQuery, match to Stripe exports in GCS, write discrepancies to a reporting table and notify finance. Must be rerunnable, partitioned by date, and cost-aware. Include schema for inputs/outputs, orchestration (e.g. Cloud Workflows / Composer—recommend), and monitoring with alerts on failure or row-count anomalies.

4. Small MVP (keeps output shorter)

MVP: single Cloud Run service exposing one POST endpoint that accepts a JSON payload, validates it, stores in Postgres, returns id. No auth for v1, but note how we’d add JWT later. Need basic tests, Dockerfile, and Terraform sketch for Cloud Run + DB.

5. Migration / rewrite

We are replacing a legacy Java servlet app that owns customer profiles with a Node.js service. Zero-downtime migration, dual-write then cutover, rollback plan. DB stays Postgres; call out migration tools, feature flags, and QA focus on data parity and session behavior.

6. Security-heavy

Greenfield B2B document portal: upload PDFs, virus scan, virus-scan pass/fail gates ingestion, store in GCS with CMEK, metadata in Postgres. Row-level access by tenant_id. Need threat model bullets, encryption at rest/in transit, and deployment with least-privilege service accounts.

How to use them in the UI
Send a short first message (e.g. Hello).
When the agent asks what you want to build, reply with one full block from the samples above (or your own), with constraints (stack, region, compliance, SLOs) so capture_requirement preserves them for the pipeline.
