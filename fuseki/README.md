Fuseki setup and load

Prereqs
- Apache Jena Fuseki installed and runnable
- kg_sample.ttl generated

Quick start (manual)
1) Start Fuseki
2) Create dataset named "kg" (via web UI)
3) Load data using upload.ps1

PowerShell upload
- Edit the variables in upload.ps1 if needed
- Run: powershell -ExecutionPolicy Bypass -File fuseki/upload.ps1

Queries
- Use files in fuseki/queries with the Fuseki UI
