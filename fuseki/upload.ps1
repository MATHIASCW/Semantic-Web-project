$ErrorActionPreference = "Stop"

$endpoint = $env:SPARQL_UPDATE_ENDPOINT
if (-not $endpoint) {
  $dataset = $env:KG_DATASET
  if (-not $dataset) { $dataset = "kg-tolkiengateway" }
  $endpoint = "http://localhost:3030/$dataset/data"
}

$dataFile = $env:KG_TTL
if (-not $dataFile) { $dataFile = "kg_sample.ttl" }

if (-not (Test-Path $dataFile)) {
  Write-Host "TTL not found: $dataFile"
  exit 1
}

Write-Host "Uploading $dataFile -> $endpoint"
curl -sS -X POST -H "Content-Type: text/turtle" --data-binary "@$dataFile" $endpoint
Write-Host "Done."
