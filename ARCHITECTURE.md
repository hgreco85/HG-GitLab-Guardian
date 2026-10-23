# GitLab Guardian — Architectural Design Specification

## Overview

GitLab Guardian is an autonomous post-code incident commander built to operate within the **GitLab Duo Agent Platform** ecosystem. It bridges the gap between raw CI/CD failures and developer intervention by transforming unhandled pipeline errors into verified, reproducible, pull-ready Merge Requests with zero security leakage.

---

## 🏛️ System Architecture

```text
               +-------------------------------------------+
               |        GitLab CI / Webhook Ingestion      |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |           Security Guard (Layer 1)         |
               | - Secret Scanner (glpat, ghp, sk, bearer) |
               | - Schema Validation (frozenset allowlist) |
               | - Fail-Closed Rejection                   |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |         GitLab Duo Agent (Layer 2)         |
               | - Log Analyzer & Causal Classifier        |
               | - Confidence Scoring Engine               |
               | - Multi-Scenario Incident Triage          |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |        Remediation Engine (Layer 3)       |
               | - Minimal Unit Reproduction Synthesis     |
               | - Surgical Diff Patch Generation          |
               | - Draft Merge Request Preparation         |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |       Decision Ledger (Compliance)        |
               | - SHA-256 Tamper-Evident Chain            |
               | - Non-Repudiation & Audit Trail           |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |        Human Approval Gate (Safety)       |
               | - Assisted Mode Enforced                  |
               | - Explicit Maintainer Sign-off Required   |
               +-------------------------------------------+
```

---

## 🔒 Security Principles

1. **Fail-Closed by Default:** Any input that deviates from strict schema limits or contains unmaskable credentials results in immediate, clean termination.
2. **Zero-Secret Reflection:** Credentials detected in logs or payloads are purged immediately. No secret is ever written to logs, ledger payloads, or MR descriptions.
3. **Assisted Execution Boundary:** The agent cannot invoke `git push --force`, auto-merge, or execute unauthorized deployments.

---

## ⚡ Performance & Resource Efficiency

- **Pure Python Standard Library:** Instant startup without heavy container layers.
- **Zero Incremental Compute Spend ($0.00 USD):** Operates entirely within standard GitLab Runner allocations.
- **Resilient Execution:** Exponential backoff with jitter prevents race conditions during transient GitLab API rate limits.
