# GitLab Guardian V1 ÔÇö offline-only

Pure Python stdlib readiness assessment. No network, tokens, billing changes, scheduled jobs, GitLab agents, GitLab CI, GitHub workflow modifications or deploys.

## Run
```sh
python -m unittest discover -s tools/gitlab_guardian -p 'test_*.py' -v
python tools/gitlab_guardian/guardian.py tools/gitlab_guardian/evidence.json
```

The known state is **BLOCK: agent_platform_unverified**. GitLab emails confirm Duo Enterprise seat and Community Members **Developer** role. They **do not** establish Agent Platform entitlement, quotas, zero-cost execution, or budget guarantees.

This is **not** an authorization system: arbitrary evidence JSON is untrusted. Even if every flag is true, `may_execute` remains false. A live runner requires authenticated read-only checks, account-level cost enforcement and separate explicit approval.

Existing `config/execution_router_v0.json` has `gitlab-ci.enabled=false` and is intentionally unchanged. No monitor rows or Control Tower states are modified by this PR.
