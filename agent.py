"""
Software Delivery Team — multi-agent ADK workflow (Solution Architect → DB Architect
→ Developer → QA → Deployment → Delivery synthesis).

Deploy with (from this package directory):
  uvx --from google-adk==1.14.0 adk deploy cloud_run \\
    --project=$PROJECT_ID --region=us-central1 \\
    --service_name=software-delivery-team --with_ui . \\
    -- --service-account=$SERVICE_ACCOUNT
"""

import logging
import os

import google.cloud.logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

# --- Logging & env (same pattern as Google ADK Cloud Run codelab) ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL", "gemini-2.5-flash")


def capture_requirement(
    tool_context: ToolContext, requirement: str
) -> dict[str, str]:
    """Persist the user's product/engineering ask into session state."""
    tool_context.state["REQUIREMENT"] = requirement
    logging.info("[State] REQUIREMENT captured (%d chars)", len(requirement))
    return {"status": "success"}


solution_architect = Agent(
    name="solution_architect",
    model=model_name,
    description="Owns context, constraints, C4-style views, NFRs, and risks.",
    instruction="""
You are a senior Solution Architect. Using only REQUIREMENT below, produce a concise
architecture brief suitable for engineers.

Include:
- Problem summary and success criteria
- Proposed components/services and how they interact (boundaries, APIs/events)
- Key non-functional requirements (security, reliability, performance, cost awareness)
- Top risks and mitigations
- Open questions for stakeholders

REQUIREMENT:
{ REQUIREMENT }
""",
    output_key="architecture",
)

database_architect = Agent(
    name="database_architect",
    model=model_name,
    description="Data modeling, storage choices, migrations, and data integrity.",
    instruction="""
You are a Database Architect. Build on the solution architecture and the original ask.

Deliver:
- Conceptual / logical model (entities, relationships)
- Storage recommendation (e.g. OLTP, cache, warehouse, object store) with rationale
- Schema sketch (tables/collections or document shapes) and indexing strategy
- Migration/backfill approach and consistency model
- Backup, retention, and PII/encryption notes

REQUIREMENT:
{ REQUIREMENT }

ARCHITECTURE:
{ architecture }
""",
    output_key="database_design",
)

developer_agent = Agent(
    name="developer_agent",
    model=model_name,
    description="Implementation plan: stack, modules, interfaces, and key code paths.",
    instruction="""
You are a Staff Software Engineer. Propose an implementation that fits the architecture
and data design.

Include:
- Recommended language/framework and repo layout
- Core modules/classes or services and their responsibilities
- Critical interfaces (REST/gRPC/events) and example payloads
- Pseudocode or short snippets only where they clarify a tricky flow
- Definition of Done for the engineering slice (build, lint, types, observability hooks)

REQUIREMENT:
{ REQUIREMENT }

ARCHITECTURE:
{ architecture }

DATABASE_DESIGN:
{ database_design }
""",
    output_key="implementation_plan",
)

qa_agent = Agent(
    name="qa_agent",
    model=model_name,
    description="Test strategy, cases, automation, and quality gates.",
    instruction="""
You are a QA Lead / Test Architect.

From the requirement, architecture, data design, and implementation plan, produce:
- Test strategy (levels: unit, integration, e2e, non-functional)
- Risk-based test priorities and edge cases
- Representative test cases (Given/When/Then) for happy path + critical failures
- Test data and environment needs
- CI quality gates (coverage thresholds if applicable, flaky test policy)
- "Release readiness" checklist

REQUIREMENT:
{ REQUIREMENT }

ARCHITECTURE:
{ architecture }

DATABASE_DESIGN:
{ database_design }

IMPLEMENTATION_PLAN:
{ implementation_plan }
""",
    output_key="qa_plan",
)

deployment_agent = Agent(
    name="deployment_agent",
    model=model_name,
    description="Delivery: environments, Cloud Run/K8s, IaC, secrets, rollback.",
    instruction="""
You are a DevOps / Platform engineer focused on safe, repeatable delivery.

Produce a deployment runbook style answer:
- Environments (dev/stage/prod) and promotion strategy
- Container/Cloud Run or GKE sketch (CPU/mem, min/max instances, concurrency)
- Secrets/config (Secret Manager, workload identity) and least privilege
- Observability (logs, metrics, traces, SLOs, alerts)
- Rollback and feature-flag strategy
- Estimated operational cost levers (scale-to-zero, caching, batching)

REQUIREMENT:
{ REQUIREMENT }

ARCHITECTURE:
{ architecture }

IMPLEMENTATION_PLAN:
{ implementation_plan }

QA_PLAN:
{ qa_plan }
""",
    output_key="deployment_plan",
)

delivery_synthesis = Agent(
    name="delivery_synthesis",
    model=model_name,
    description="Single cohesive handoff doc for humans.",
    instruction="""
You are the Delivery Lead. Merge the prior agent outputs into ONE readable document
for a product/engineering review.

Structure:
1) Executive summary (5 bullets max)
2) Architecture highlights
3) Data design highlights
4) Engineering plan highlights
5) QA / release readiness highlights
6) Deployment & operations highlights
7) Decisions needed / open questions

Use clear headings and bullet lists. Do not repeat verbatim; synthesize and de-duplicate.

REQUIREMENT:
{ REQUIREMENT }

ARCHITECTURE:
{ architecture }

DATABASE_DESIGN:
{ database_design }

IMPLEMENTATION_PLAN:
{ implementation_plan }

QA_PLAN:
{ qa_plan }

DEPLOYMENT_PLAN:
{ deployment_plan }
""",
)

software_delivery_pipeline = SequentialAgent(
    name="software_delivery_pipeline",
    description="Runs architect → data → dev → QA → deployment → synthesis in order.",
    sub_agents=[
        solution_architect,
        database_architect,
        developer_agent,
        qa_agent,
        deployment_agent,
        delivery_synthesis,
    ],
)

root_agent = Agent(
    name="delivery_intake",
    model=model_name,
    description="Entry point for the software delivery multi-agent team.",
    instruction="""
You coordinate a virtual software delivery team.

- Briefly introduce the roles (Solution Architect, DB Architect, Developer, QA,
  Deployment) and ask what the user wants to build or improve.
- When the user describes their need, call the tool `capture_requirement` with their
  full text (do not summarize away important constraints).
- After the tool succeeds, transfer to the `software_delivery_pipeline` agent so the
  specialists can run in sequence.

Keep the first reply short; the pipeline will produce the long-form plan.
""",
    tools=[capture_requirement],
    sub_agents=[software_delivery_pipeline],
)
