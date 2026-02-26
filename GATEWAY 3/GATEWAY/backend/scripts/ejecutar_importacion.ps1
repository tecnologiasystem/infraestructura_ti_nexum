# Script PowerShell para importar CSV
# Ejecutar con: .\scripts\ejecutar_importacion.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Importacion de CSV a SQL Server" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Ir a la carpeta del proyecto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath
Set-Location $projectPath

Write-Host "📂 Ubicación: $projectPath" -ForegroundColor Yellow
Write-Host ""

# Verificar que existe el entorno virtual
if (-not (Test-Path ".\env\Scripts\python.exe")) {
    Write-Host "❌ Error: No se encuentra el entorno virtual en .\env" -ForegroundColor Red
    Write-Host "   Ejecuta primero: python -m venv env" -ForegroundColor Yellow
    pause
    exit 1
}

# Ejecutar el script de Python
Write-Host "🚀 Ejecutando importación..." -ForegroundColor Green
Write-Host ""

& ".\env\Scripts\python.exe" ".\scripts\importar_rapido.py"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Presiona cualquier tecla para salir..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
