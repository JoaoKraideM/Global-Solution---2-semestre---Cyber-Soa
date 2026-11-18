# Execute na raiz do projeto: powershell -ExecutionPolicy Bypass -File scripts/iniciar_demo.ps1
$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.env')) { & "$PSScriptRoot/preparar_env.ps1" }
$envLines = Get-Content '.env'
if ($envLines -match '^\s*DB_USER\s*=\s*root\s*$') { throw 'DB_USER=root não é aceito como usuário de aplicação MySQL 8.4; use um usuário regular como sombraviva.' }
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar Docker. Consulte docker compose logs mysql api.' }
docker compose ps
docker compose exec -T api python -m scripts.check_mysql
if ($LASTEXITCODE -ne 0) { throw 'Banco incompleto: confira docker compose logs api --tail=100.' }
docker compose exec -T api python -m scripts.exportar_evidencias
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível gerar as evidências de exemplo.' }
New-Item -ItemType Directory -Force -Path 'evidencias' | Out-Null
docker compose cp api:/usr/src/app/evidencias/evidencias_soa_cyber_demo.json ./evidencias/evidencias_soa_cyber_demo.json
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível copiar o JSON de evidência para Windows.' }
Write-Host 'SombraViva: http://localhost:8000 | Admin SOC: http://localhost:8000/admin | Swagger: http://localhost:8000/docs'
Write-Host 'No admin, selecione: Explorar casos fictícios e análise. Eventos reais permanecem separados.'
