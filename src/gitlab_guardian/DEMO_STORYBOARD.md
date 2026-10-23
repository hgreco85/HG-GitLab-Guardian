# Guardian V2 ÔÇö three-incident offline demo
Run `python tools/gitlab_guardian/demo_three_incidents.py` locally or from the safe CI gate.
All names, incidents and credentials in the demonstration are fictional.

**Scene 1 / Broken pipeline:** mock labels it `ci_failure` and proposes a manual log review. No fix is committed.
**Scene 2 / Dependency advisory:** mock labels it `security_review` and requires a security-owner decision. No real project or vulnerability is scanned.
**Scene 3 / Contaminated output:** mock refuses to process a credential-shaped string and returns `BLOCK/sensitive_data` without reflecting the string.

**Audience note:** this demonstrates guardrails and a deterministic simulation, **not** the real GitLab Duo Agent Platform. It is not contest-submission compliant by itself. No network, billing, merge, deploy or publication is performed.
