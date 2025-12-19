$ErrorActionPreference = "Stop"

$dataset = $env:KG_DATASET
if (-not $dataset) { $dataset = "kg-tolkiengateway" }

Write-Host "Generating TTL..."
python testApiRequestWithoutFastApi/requestAll.py

Write-Host "Uploading to Fuseki dataset '$dataset'..."
$env:KG_DATASET = $dataset
powershell -ExecutionPolicy Bypass -File fuseki/upload.ps1

Write-Host "Done."
