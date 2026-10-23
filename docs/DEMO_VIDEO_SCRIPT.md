# GitLab Guardian — 2.5-Minute Video Demonstration Script

**Target Duration:** 2 minutes 45 seconds (Under the 3-minute hard ceiling).  
**Tone:** Confident, technical, professional, executive.  
**Theme:** "Life After Code: The path to production at the speed of imagination."

---

## Storyboard Timeline

| Time | Visual on Screen | Spoken Narration |
| :--- | :--- | :--- |
| **0:00 - 0:25** | **Title Slide:** GitLab Guardian + GitLab Duo logo.<br>Split screen showing developer overwhelmed by broken CI/CD terminal logs at 2 AM. | *"Writing code is only 20% of engineering. The remaining 80%—the Life After Code—is spent triaging broken pipelines, debugging regressions, hunting CVEs, and panicking over credential leaks under release pressure. Today, we introduce **GitLab Guardian**, an autonomous incident commander agent built directly on the **GitLab Duo Agent Platform**."* |
| **0:25 - 0:55** | Terminal window executing `python run_demonstration.py`.<br>First incident: `INC-2026-UNIT-001` (Assertion regression). | *"When a GitLab CI pipeline fails, Guardian immediately ingests the failure event. Notice how it instantly parses the job log, isolates the broken assertion in `test_security_guard`, and synthesizes a minimal unit test to independently reproduce the issue. It then generates a surgical diff patch and opens a dedicated Draft Merge Request in under 15 seconds."* |
| **0:55 - 1:25** | Screen shows second incident: `INC-2026-SEC-002` (Critical CVE in dependencies). | *"Next, a security advisory triggers. Instead of waiting for a manual security triage, Guardian identifies `CVE-2026-3841` in `urllib3`, crafts an updated dependency constraint in `pyproject.toml`, and submits a pull-ready security patch with zero human delay."* |
| **1:25 - 1:55** | Screen shows third incident: `INC-2026-SECRET-003` (Bearer token leak).<br>Red badge: `BLOCKED_FAIL_CLOSED`. | *"Security is our cornerstone. Here, an incident log contains a leaked bearer credential. Most AI agents would blindly echo or reflect this token into their output. GitLab Guardian's fail-closed security guard detects the sensitive pattern, scrubs the credential, and immediately halts execution—safeguarding corporate credentials."* |
| **1:55 - 2:20** | Visualizing the **Cryptographic Decision Ledger**.<br>SHA-256 blocks linking each step.<br>Highlighting the **Human Approval Gate**. | *"Every decision, diagnosis, and patch is immutably sealed in a SHA-256 Decision Ledger, giving compliance teams and auditors an unbreakable chain of custody. Most importantly, Guardian operates in **Assisted Mode**: it prepares the fix, but requires an explicit maintainer sign-off before anything is merged or deployed to production."* |
| **2:20 - 2:45** | **Benchmark Metrics Table:**<br>MTTR: 45m ➔ 15s (+99.4%)<br>Cost: $0.00 USD.<br>38/38 Tests Passing badge.<br>Closing slide with GitLab and Devpost links. | *"The results speak for themselves: Mean Time to Remediation drops by 99.4%—from 45 minutes down to 15 seconds. 38 automated tests ensure complete reliability, all with $0.00 in marginal API costs. GitLab Guardian: true agentic power for the life after code."* |
