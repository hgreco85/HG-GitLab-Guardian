# AGENTS.md — GitLab Duo Agent Platform Context & Instructions

This repository is optimized for autonomous post-code incident management using the **GitLab Duo Agent Platform**.

## Project Context
- **Name:** GitLab Guardian
- **Domain:** Autonomous Post-Code Incident Commander
- **Target SDLC Phase:** Post-code (Testing, CI/CD triage, Dependency Security, Secret Sanitization, Merge Request Creation)
- **Execution Mode:** Assisted (Human maintainer sign-off required for all merges and deployments)
- **Marginal Cost Boundary:** $0.00 USD (Pure standard library / Free-First)

## Commands for GitLab Duo Agents
- **Run Full Test Suite:** `python -m unittest discover -s tests -p 'test_*.py' -v`
- **Run Standalone Demonstration:** `python run_demonstration.py`
- **Run Empirical Benchmark (N=200):** `python -m gitlab_guardian.benchmark_suite`

## Agentic Operational Boundaries
1. **Zero Secret Reflection:** Never echo, log, or persist detected credentials (`glpat-*`, `ghp_*`, `sk-*`, bearer tokens, private keys).
2. **Deterministic Triage:** When triaging failed CI jobs, classify causal categories into:
   - `TEST_REGRESSION`: Unit test assertion failure.
   - `SECURITY_ADVISORY`: High/Critical CVE in dependencies.
   - `SECRET_LEAKAGE`: Credentials found in job log or build artifacts.
   - `PIPELINE_FAILURE`: Runner, environment, or syntax failure.
3. **Reproducibility First:** Before proposing any patch, synthesize a minimal reproducible unit test that independently fails on the unfixed code and passes after the patch is applied.
4. **Human Approval Gate:** Always output a Maintainer Sign-Off checklist in the proposed Merge Request. Never attempt to merge autonomously.
