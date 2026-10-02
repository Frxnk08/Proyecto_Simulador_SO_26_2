New-Item -ItemType Directory -Force -Path logs | Out-Null
for ($i = 1; $i -le 20; $i++) {
    $num = $i.ToString("00")
    python productor_consumidor.py > "logs/corrida_$num.txt" 2>&1
}
Write-Host "=== RESUMEN DE LAS 20 CORRIDAS ==="
Select-String -Path "logs/corrida_*.txt" -Pattern "RESULTADO"