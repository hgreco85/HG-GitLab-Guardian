# Guía de Sincronización GitLab Guardian V2 vía ChatGPT / GitLab API

**Proyecto Destino:** `hg-stack-group/hg-stack-project` (`https://gitlab.com/hg-stack-group/hg-stack-project`)  
**Rama Aislada:** `feature/gitlab-guardian-v2-transcend` (creada desde `main`)  
**Commit de Origen en GitHub:** [`3864e8b86aa7aec4c12d261071597992e937e53a`](https://github.com/hgreco85/HG-GitLab-Guardian/commit/3864e8b86aa7aec4c12d261071597992e937e53a)  
**Manifest JSON Oficial:** [`GITLAB_SYNC_MANIFEST.json`](GITLAB_SYNC_MANIFEST.json)  

---

## 🎯 Instrucciones de Ejecución desde ChatGPT (con Conexión GitLab)

Dado que ChatGPT dispone de integración directa con la API de GitLab, ejecutá las siguientes 4 operaciones secuenciales para sincronizar la nueva versión sin tocar `main` ni interferir con otros proyectos:

### Paso 1: Crear la rama aislada
- **Acción GitLab:** Crear rama en el proyecto `hg-stack-group/hg-stack-project`.
- **Nombre de la Rama:** `feature/gitlab-guardian-v2-transcend`
- **Ref / Rama Base:** `main`
- *Endpoint API:* `POST /api/v4/projects/hg-stack-group%2Fhg-stack-project/repository/branches?branch=feature/gitlab-guardian-v2-transcend&ref=main`

### Paso 2: Crear el Commit con todos los archivos de Guardian V2
- **Acción GitLab:** Enviar un commit masivo con las 37 acciones de archivo.
- **Rama:** `feature/gitlab-guardian-v2-transcend`
- **Mensaje de Commit:** `feat(guardian): integrate GitLab Guardian V2 with GitLab Duo Agent Platform`
- **Acciones:** Utilizar el array `gitlab_api_spec.step_2_commit_files.body.actions` de [`GITLAB_SYNC_MANIFEST.json`](GITLAB_SYNC_MANIFEST.json).

### Paso 3: Disparar el Pipeline de CI/CD
- **Acción GitLab:** Iniciar pipeline en la rama recién creada.
- **Rama:** `feature/gitlab-guardian-v2-transcend`
- *Endpoint API:* `POST /api/v4/projects/hg-stack-group%2Fhg-stack-project/pipeline?ref=feature/gitlab-guardian-v2-transcend`
- **Verificación:** Monitorear que el pipeline ejecute los 4 jobs (`lint:syntax`, `test:unit`, `security:secret-detection`, `guardian:e2e-simulation`).

### Paso 4: Crear la Draft Merge Request
- **Acción GitLab:** Crear Merge Request.
- **Source Branch:** `feature/gitlab-guardian-v2-transcend`
- **Target Branch:** `main`
- **Título:** `Draft: feat(guardian): GitLab Guardian V2 — Post-Code Incident Commander`
- **Descripción:** Texto estructurado provisto en `gitlab_api_spec.step_4_create_draft_mr.body.description`.

---

## 📋 Lista de Archivos en el Manifest (37 archivos)

| Archivo | Tamaño (bytes) | Hash SHA-256 |
| :--- | :--- | :--- |
| `.gitlab/duo/agent-config.yml` | 583 | `d8055f006cfecb48...` |
| `.gitlab/duo/agent.yml` | 1,602 | `ea789209ea3e0416...` |
| `.gitlab-ci.yml` | 1,577 | `43601166f43f2911...` |
| `AGENTS.md` | 1,697 | `fe23121eec468256...` |
| `README.md` | 8,535 | `9e711dd7ff964cff...` |
| `ARCHITECTURE.md` | 3,590 | `87e4b9fa10f28e8f...` |
| `DEVPOST_SUBMISSION.md` | 6,844 | `e88233d7dda9c8d6...` |
| `LICENSE` | 1,065 | `5cfdbd9126bdb2f3...` |
| `run_demonstration.py` | 6,988 | `09b2f06c75cc014d...` |
| `evidence_demonstration.json` | 7,957 | `026dce27796db3fe...` |
| `docs/DEMO_VIDEO_SCRIPT.md` | 3,177 | `e9e2e9bc8c942144...` |
| `src/gitlab_guardian/__init__.py` | 166 | `2bf6892d04fad112...` |
| `src/gitlab_guardian/duo_agent.py` | 4,692 | `dd9308537d9cf54f...` |
| `src/gitlab_guardian/pipeline_triage.py` | 4,732 | `a18f331cc70f217d...` |
| `src/gitlab_guardian/remediation.py` | 5,481 | `867313f528a35dc2...` |
| `src/gitlab_guardian/security_guard.py` | 2,287 | `66e61a2c502919bc...` |
| `src/gitlab_guardian/ledger.py` | 2,983 | `1f8a0b398ce8bdf4...` |
| `src/gitlab_guardian/workflow_engine.py` | 4,881 | `7797434a32f77562...` |
| `src/gitlab_guardian/benchmark_suite.py` | 4,912 | `296e1325af63aaf4...` |
| `src/gitlab_guardian/metrics.py` | 2,079 | `23d5726d6c31077f...` |
| `src/gitlab_guardian/guardian.py` | 1,596 | `edb066d109158f4e...` |
| `src/gitlab_guardian/transcend_v2.py` | 1,817 | `074bc68cf1024065...` |
| `src/gitlab_guardian/mock_agent.py` | 960 | `65119e8228aae921...` |
| `src/gitlab_guardian/benchmark.py` | 1,459 | `bde017da28e8498b...` |
| `src/gitlab_guardian/demo_three_incidents.py` | 1,365 | `a31c72561c003cc0...` |
| `tests/test_flow_e2e.py` | 2,676 | `d176f8757b69fb34...` |
| `tests/test_duo_agent.py` | 2,286 | `c6369b203a40e3e0...` |
| `tests/test_ledger.py` | 1,471 | `48a6132dc44edde9...` |
| `tests/test_guardian.py` | 2,382 | `4b1c733e80029c4f...` |
| `tests/test_transcend_v2.py` | 1,272 | `f5377acff9a60db0...` |
| `tests/test_security_v2.py` | 2,064 | `626af066cb3062a6...` |
| `tests/test_mock_benchmark.py` | 888 | `ec65e69d17be7eed...` |
| `tests/test_demo_three_incidents.py` | 998 | `6d63dd3d767f6b5b...` |
| `fixtures/incident_1_assertion_failure.json` | 501 | `58e5a6deaa317969...` |
| `fixtures/incident_2_security_advisory.json` | 399 | `326d5c716a653335...` |
| `fixtures/incident_3_secret_leak_blocked.json` | 359 | `2e3c1ea2c6787667...` |
| `fixtures/gitlab_duo_chat_webhook.json` | 315 | `62156890f39fb851...` |
