# Cria um .env local com segredos criptograficamente aleatórios, apenas se ele não existir.
# NÃO envia credenciais ao GitHub e NÃO altera um .env anterior.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root '.env'
if (Test-Path $target) {
  Write-Host 'Seu .env já existe e foi preservado. Nenhuma senha foi alterada.'
  exit 0
}
$template = Join-Path $root '.env.example'
if (-not (Test-Path $template)) { throw 'Arquivo .env.example ausente.' }
function New-Hex([int]$count) {
  $bytes = New-Object byte[] $count
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
  return -join ($bytes | ForEach-Object { $_.ToString('x2') })
}
$content = [System.IO.File]::ReadAllText($template)
$values = @{
  'SUBSTITUA_POR_SENHA_FORTE_DO_MYSQL' = (New-Hex 24)
  'SUBSTITUA_POR_SENHA_ROOT_DIFERENTE' = (New-Hex 24)
  'SUBSTITUA_POR_CHAVE_ALEATORIA_COM_32_CARACTERES_OU_MAIS' = (New-Hex 32)
  'SUBSTITUA_POR_SENHA_FORTE_ADMIN' = (New-Hex 20)
  'SUBSTITUA_POR_CHAVE_SEGURA_SENSOR_A' = (New-Hex 32)
  'SUBSTITUA_POR_CHAVE_SEGURA_SENSOR_B' = (New-Hex 32)
}
foreach ($name in $values.Keys) { $content = $content.Replace($name, $values[$name]) }
[System.IO.File]::WriteAllText($target, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Host 'Arquivo .env criado com valores aleatórios. Guarde-o fora do GitHub.'
Write-Host 'O acesso administrativo está em ADMIN_EMAIL / ADMIN_PASSWORD dentro do .env local.'
Write-Host 'Importante: se já havia um volume MySQL inicializado com outras senhas, restaure as credenciais originais; não apague o volume.'
