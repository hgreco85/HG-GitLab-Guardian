# Instrucción Lista para Pegar en ChatGPT (con Conexión GitLab)

Copia y pega el siguiente bloque de texto en tu conversación con ChatGPT para que ejecute la sincronización oficial con la API de GitLab:

```markdown
Por favor, utiliza tu herramienta de integración con GitLab para sincronizar el proyecto HG-GitLab-Guardian V2 con el repositorio de GitLab oficial, siguiendo estos pasos exactos:

1. **Proyecto Destino**: `hg-stack-group/hg-stack-project` (o ID de proyecto correspondiente).
2. **Crear Rama Aislada**:
   - Nombre de la rama: `feature/gitlab-guardian-v2-transcend`
   - Rama base (ref): `main`
   - *Nota*: No modificar `main` directamente.

3. **Publicar Archivos mediante Commit**:
   - Lee el manifest JSON publicado en GitHub:
     `https://raw.githubusercontent.com/hgreco85/HG-GitLab-Guardian/main/GITLAB_SYNC_MANIFEST.json`
   - Ejecuta un commit masivo en la rama `feature/gitlab-guardian-v2-transcend` con las 37 acciones de archivos contenidas en el JSON (`gitlab_api_spec.step_2_commit_files.body.actions`).
   - Mensaje de commit: `feat(guardian): integrate GitLab Guardian V2 with GitLab Duo Agent Platform`

4. **Disparar Pipeline CI/CD**:
   - Dispara un nuevo pipeline sobre la rama `feature/gitlab-guardian-v2-transcend`.
   - Espera o reporta el `id`, `web_url` y estado de los jobs (`lint:syntax`, `test:unit`, `security:secret-detection`, `guardian:e2e-simulation`).

5. **Crear Draft Merge Request**:
   - Source branch: `feature/gitlab-guardian-v2-transcend`
   - Target branch: `main`
   - Título: `Draft: feat(guardian): GitLab Guardian V2 — Post-Code Incident Commander`
   - Descripción:
     ```
     ## GitLab Guardian V2 — Post-Code Incident Commander
     ### Transcend: Life After Code Hackathon Entry

     - **Specification**: `.gitlab/duo/agent-config.yml` (GitLab Duo Agent Platform)
     - **Context Graph**: `AGENTS.md` (GitLab Orbit)
     - **Empirical Benchmark**: N=200 deterministic cases (100% accuracy, 100% adversarial secret detection)
     - **CI/CD Stages**: lint, test, security-scan, guardian-verify
     - **Human Approval Gate**: Enabled (strict fail-closed, no auto-merge without maintainer sign-off)
     ```

6. **Devolver Evidencia**:
   - Proporciona la URL del commit en GitLab, la URL del pipeline ejecutado y la URL de la Draft Merge Request creada.
```
