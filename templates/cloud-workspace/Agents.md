# Workspace Agent Context

This workspace contains two projects.

## v2-portal
- **Path:** `./v2-portal`
- **Type:** Next.js web application (TypeScript)
- **Role:** The frontend portal. This is the UI layer that communicates with the backend API.

## cloud_backend
- **Path:** `./cloud_backend`
- **Type:** .NET microservices solution
- **Role:** The backend API layer. Structured as a set of microservices (Auth, Brand, ExternalIntegration, Invoicing, Lookup, Menu, OnlineOrdering, Payment) behind a single Gateway.
- **Primary solution file:** `AuraServices.sln` — this repo contains multiple `.sln` files. **Always** specify `AuraServices.sln` explicitly for any dotnet command (restore, build, test, run, publish, etc.). Running dotnet without a target will fail.
  ```
  dotnet restore AuraServices.sln
  dotnet build AuraServices.sln
  dotnet test AuraServices.sln
  ```
