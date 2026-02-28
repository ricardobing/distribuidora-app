# seed_remitos.ps1 - Crea 12 remitos realistas de Mendoza para pruebas
$base = "http://localhost:8000/api/v1"

$loginBody = '{"email":"admin@molymarket.com","password":"admin1234"}'
$token = (Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body $loginBody).access_token
$headers = @{Authorization="Bearer $token"; "Content-Type"="application/json"}

$remitos = @(
  @{numero="R002"; domicilio="Belgrano 1200, Godoy Cruz, Mendoza"; cliente="Fernandez Ana"; telefono="2614001002"; observaciones="andreani"; es_urgente=$true; es_prioridad=$false},
  @{numero="R003"; domicilio="Rivadavia 890, Guaymallen, Mendoza"; cliente="Lopez Carlos"; telefono="2614001003"; observaciones="OCA express"; es_urgente=$false; es_prioridad=$false},
  @{numero="R004"; domicilio="Colon 345, Las Heras, Mendoza"; cliente="Martinez Sofia"; telefono="2614001004"; observaciones="retira en galpon"; es_urgente=$false; es_prioridad=$true},
  @{numero="R005"; domicilio="Dorrego 678, Guaymallen, Mendoza"; cliente="Rodriguez Juan"; telefono="2614001005"; observaciones="via cargo"; es_urgente=$false; es_prioridad=$false},
  @{numero="R006"; domicilio="Aristides Villanueva 234, Ciudad, Mendoza"; cliente="Gonzalez Maria"; telefono="2614001006"; observaciones="Envio Propio urgente"; es_urgente=$true; es_prioridad=$true},
  @{numero="R007"; domicilio="Emilio Civit 512, Ciudad, Mendoza"; cliente="Torres Luis"; telefono="2614001007"; observaciones="andreani"; es_urgente=$false; es_prioridad=$false},
  @{numero="R008"; domicilio="Mitre 1100, Godoy Cruz, Mendoza"; cliente="Diaz Paula"; telefono="2614001008"; observaciones="correo argentino"; es_urgente=$false; es_prioridad=$false},
  @{numero="R009"; domicilio="Montevideo 430, Guaymallen, Mendoza"; cliente="Ramirez Pedro"; telefono="2614001009"; observaciones="OCA"; es_urgente=$true; es_prioridad=$false},
  @{numero="R010"; domicilio="Paso de los Andes 890, Las Heras, Mendoza"; cliente="Sanchez Laura"; telefono="2614001010"; observaciones="Envio Propio"; es_urgente=$false; es_prioridad=$false},
  @{numero="R011"; domicilio="Olascoaga 750, Ciudad, Mendoza"; cliente="Alvarez Diego"; telefono="2614001011"; observaciones="viene a buscar"; es_urgente=$false; es_prioridad=$false},
  @{numero="R012"; domicilio="Bandera de los Andes 320, Guaymallen, Mendoza"; cliente="Romero Claudia"; telefono="2614001012"; observaciones="urbano express"; es_urgente=$false; es_prioridad=$true}
)

Write-Host ""
Write-Host "=== INGESTING REMITOS ===" -ForegroundColor Cyan
foreach ($r in $remitos) {
  $body = @{
    numero       = $r.numero
    domicilio    = $r.domicilio
    cliente      = $r.cliente
    telefono     = $r.telefono
    observaciones = $r.observaciones
    es_urgente   = $r.es_urgente
    es_prioridad = $r.es_prioridad
  } | ConvertTo-Json

  try {
    $res = Invoke-RestMethod -Uri "$base/remitos/" -Method POST -Headers $headers -Body $body
    $status = "OK"
    Write-Host "  $status $($r.numero) -> id=$($res.id) carrier='$($res.carrier_nombre)' clasi='$($res.estado_clasificacion)'"
  } catch {
    $msg = $_.Exception.Message
    Write-Host "  ERR $($r.numero) -> $msg" -ForegroundColor Red
  }
}

Write-Host ""
Write-Host "=== ESTADO ACTUAL ===" -ForegroundColor Cyan
$all = Invoke-RestMethod -Uri "$base/remitos/?limit=50" -Headers $headers
Write-Host "Total remitos: $($all.total)"
$all.items | Group-Object carrier_nombre | Sort-Object Count -Descending | ForEach-Object {
  Write-Host "  $($_.Count)x $($_.Name)"
}

Write-Host ""
Write-Host "=== DASHBOARD ===" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$base/dashboard/" -Headers $headers | ConvertTo-Json -Depth 3
