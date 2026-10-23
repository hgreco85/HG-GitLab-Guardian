# sync_to_gitlab.ps1
# Sincroniza la version actualizada de GitLab Guardian con el proyecto oficial en GitLab.com
# Dispara el pipeline .gitlab-ci.yml y registra los artefactos para GitLab Duo Agent Platform.

param(
    [Parameter(Mandatory=$false)]
    [string]$GitLabToken = $env:GITLAB_TOKEN
)

$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoDir

Write-Host "=========================================================="
Write-Host "  GITLAB GUARDIAN — SINCRONIZACION OFICIAL CON GITLAB.COM"
Write-Host "  Target Project: https://gitlab.com/hg-stack-group/hg-stack-project"
Write-Host "=========================================================="

if (-not $GitLabToken) {
    Write-Host "`nPor favor ingrese su GitLab Personal Access Token (o presione Enter para autenticacion interactiva):" -ForegroundColor Cyan
    $GitLabToken = Read-Host "GitLab Token (glpat-...)"
}

if ($GitLabToken) {
    $remoteUrl = "https://oauth2:${GitLabToken}@gitlab.com/hg-stack-group/hg-stack-project.git"
    git remote set-url gitlab $remoteUrl
    Write-Host "Remote 'gitlab' configurado con autenticacion por token." -ForegroundColor Green
} else {
    git remote set-url gitlab "https://gitlab.com/hg-stack-group/hg-stack-project.git"
    Write-Host "Utilizando autenticacion por defecto del sistema."
}

Write-Host "`n[1/3] Verificando estado local..."
git status

Write-Host "`n[2/3] Empujando codigo actualizado (main) a GitLab..."
git push gitlab main --force

Write-Host "`n[3/3] Codigo sincronizado exitosamente en GitLab."
Write-Host "• Pipeline oficial: https://gitlab.com/hg-stack-group/hg-stack-project/-/pipelines"
Write-Host "• GitLab Duo Agent Config: https://gitlab.com/hg-stack-group/hg-stack-project/-/blob/main/.gitlab/duo/agent-config.yml"
Write-Host "• AGENTS.md Context: https://gitlab.com/hg-stack-group/hg-stack-project/-/blob/main/AGENTS.md"
Write-Host "=========================================================="
