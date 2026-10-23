# Guardian V2 ÔÇö competitive Path A architecture (design only)

## Distinctive demo: Explainable Post-Code Incident Commander

New project, created specifically for Life After Code. Do **not** publish or import HG-Market-System.
Offline demo accepts *synthetic* failed GitLab pipeline events and emits a deterministic review queue.
A future GitLab Duo Agent Platform flow would take bounded context, diagnose root causes and propose
unit tests and a merge request draft. Humans approve every change; no auto-merge or deploy.

**Components**
1. Webhook/event ingress (future, disabled now), strict schema, signature/identity verification and de-duplication.
2. Local fail-closed policy gate: validate project allowlist, evidence provenance, budget & agent entitlement.
3. Deterministic triage: incident class, severity, redacted failure signature, actionable human review.
4. Future GitLab agent/flow: read-only log analysis and proposed test diff; least privilege; bounded steps and tokens.
5. Evaluation harness: synthetic seeded failures (dependency drift, flaky test, permissions, leaked token, missing required job), expected diagnosis, regression pass rate, false positive rate, latency, evidence hash.
6. Human approval UI; demonstrable lifecycle CI history only after permissions and cost checks.

**Security invariants**
- No runtime based on arbitrary `evidence.json` attestations.
- GitLab API secret/CI variables never copied into public repository or logs.
- Agent Platform calls default disabled; no trials/on-demand credit purchases.
- Independent budget enforcement must be proven before any credit-consuming step; zero-cost requirement wins over contest timeline.
- No code writing, MR creation, merge, or deployment until explicitly separately authorized.

**Submission gap**
Path A requires an actual GitLab Duo Agent Platform agent/flow/MCP contribution. Current Python prototype does not satisfy that. Registration on Devpost and GitLab Contributors Platform must be confirmed via authenticated account. New public MIT GitLab repo and public CI evidence only after separate approval; deployment optional.

**Next offline tests**
- Malformed-event invariants and idempotence for duplicate IDs.
- Full redaction on request body and output, not merely keyword matching.
- Budget/entitlement provenance; mock agent adapter with fixed replies.
- Seeded benchmark and adversarial regression report.
