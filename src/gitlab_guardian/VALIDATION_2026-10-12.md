# Guardian V2 offline validation ÔÇö 2026-10-12

## Scope
PR #1407, branch `feature/gitlab-guardian-v1-offline`. Prior CI run #1940 for `cca877912d6d1d0ff5bd147e94708bc47f0bdacc` concluded **success** but did not reveal the dedicated Guardian unit test run.

## Reproduced test
Run `python -m unittest discover -s tools/gitlab_guardian -p 'test_*.py' -v` on a faithful local transcription of the four test modules and associated runtime modules fetched from the commit above. This uncovered **22 passed / 1 failed**: `test_invalid_event_never_invokes_agent` expected BLOCK for `token=xyz`, but generic token assignments were not caught.

## Fix
Update the sensitive-data expression in `transcend_v2.py` to reject `token[ \\t]*[:=]` (in addition to the existing credential patterns). The first attempted escape-only patch was superseded by the explicit character-class patch. After updating the local reproduction, **23 tests passed / 0 failures**. Synthetic benchmark: eight deterministic cases, all passed (covered within the test suite).

## Scope and limits
Local reproduction was created by transcribing fetched GitHub file contents into a fresh Python stdlib-only working directory. It is not a cryptographic byte-for-byte checkout of the repository; the GitHub workflow must independently confirm the exact branch state. No GitLab API calls, external model providers, billing, deploys or merge actions were invoked by this test suite.

## Reproduction commands
```bash
python -m unittest discover -s tools/gitlab_guardian -p 'test_*.py' -v
python tools/gitlab_guardian/benchmark.py
```

Expected: 23 tests, OK; benchmark 8/8. The underlying deterministic fuzz test runs 500 seeded adversarial inputs.

## Remaining gates
- Verify `required-ci` against **final commit** containing this evidence and the corrected expression.
- Prove Guardian-specific test suite runs in CI (general `required-ci` success alone is not sufficient).
- GitLab Agent Platform entitlement/credits and CodaBench Agenthon T2 final status remain unverified; never infer from local evidence.
