New-Item -ItemType Directory -Force -Path logsf | Out-Null

for ($i = 1; $i -le 20; $i++) {
    $num = $i.ToString("00")
    Write-Host "Ejecutando corrida $num de 20..." -ForegroundColor Cyan
    python modulo_filosofos_comensales.py > "logsf/corrida_filosofos_$num.txt" 2>&1
}

Write-Host ""
Write-Host "=== RESUMEN DE LAS 20 CORRIDAS (FILOSOFOS COMENSALES) ===" -ForegroundColor Green
Select-String -Path "logsf/corrida_filosofos_*.txt" -Pattern "RESULTADO"