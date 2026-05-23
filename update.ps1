# ==============================================================================
# SCRIPT DE ATUALIZAÇÃO AUTOMÁTICA E DEPLOY (GITOPS PIPELINE)
# ==============================================================================
Clear-Host
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " PIPELINE DE ATUALIZAÇÃO PLATAFORMA " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Carrega as variáveis do arquivo .env para o script saber a branch alvo
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            New-Item -Path "env:\$name" -Value $value -Force | Out-Null
        }
    }
    Write-Host "[+] Arquivo .env carregado com sucesso." -ForegroundColor Green
} else {
    Write-Host "[-] Erro: Arquivo .env não encontrado na raiz." -ForegroundColor Red
    Exit
}

# 2. Sincronização com o Repositório GitHub
Write-Host "`n[*] Sincronizando código com o GitHub ($env:GIT_REMOTE_ORIGIN/$env:GIT_TARGET_BRANCH)..." -ForegroundColor Yellow
git fetch $env:GIT_REMOTE_ORIGIN
git pull $env:GIT_REMOTE_ORIGIN $env:GIT_TARGET_BRANCH

if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Erro ao executar o Git Pull. Verifique o repositório." -ForegroundColor Red
    Exit
}
Write-Host "[+] Código atualizado com o repositório remoto." -ForegroundColor Green

# 3. Derruba a infraestrutura antiga limpa os volumes órfãos
Write-Host "`n[*] Parando contêineres ativos e limpando ambiente..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# 4. Reconstrói as imagens e levanta o ecossistema em background (detached mode)
Write-Host "`n[*] Compilando código fonte e reconstruindo imagens Docker..." -ForegroundColor Yellow
docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Falha crítica no build dos contêineres Docker." -ForegroundColor Red
    Exit
}

# 5. Validação de Sucesso
Write-Host "`n==================================================" -ForegroundColor Green
Write-Host " INFRAESTRUTURA ATUALIZADA E ONLINE! " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "-> Dashboard SOC : http://localhost:$env:PORT_JAVA_BACKEND" -ForegroundColor White
Write-Host "-> Prometheus    : http://localhost:$env:PORT_PROMETHEUS" -ForegroundColor White
Write-Host "-> Grafana SOC   : http://localhost:$env:PORT_GRAFANA" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Green
