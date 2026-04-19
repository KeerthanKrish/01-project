# Test script for MCP Convex Bridge Server
Write-Host ""
Write-Host "=== Testing MCP Convex Bridge ===" -ForegroundColor Cyan

# Get the AUTH_TOKEN from .env file
$authToken = "dev-test-token-change-in-production"

# Test 1: Health Check (no auth)
Write-Host ""
Write-Host "1. Testing /health endpoint (no auth required)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:3000/health" -Method Get
    Write-Host "Success: Health check passed" -ForegroundColor Green
    $response | ConvertTo-Json
}
catch {
    Write-Host "Failed: Health check failed: $_" -ForegroundColor Red
}

# Test 2: SSE without auth (should fail)
Write-Host ""
Write-Host "2. Testing /sse without auth (should return 401)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/sse?clientId=test-1" -Method Get -ErrorAction Stop
    Write-Host "Failed: Should have returned 401 but got: $($response.StatusCode)" -ForegroundColor Red
}
catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "Success: Correctly returned 401 Unauthorized" -ForegroundColor Green
    }
    else {
        Write-Host "Failed: Unexpected error: $_" -ForegroundColor Red
    }
}

# Test 3: Messages without auth (should fail)
Write-Host ""
Write-Host "3. Testing /messages without auth (should return 401)..." -ForegroundColor Yellow
try {
    $body = @{
        jsonrpc = "2.0"
        id = 1
        method = "ping"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:3000/messages?clientId=test-1" -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Host "Failed: Should have returned 401 but got: $($response.StatusCode)" -ForegroundColor Red
}
catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "Success: Correctly returned 401 Unauthorized" -ForegroundColor Green
    }
    else {
        Write-Host "Failed: Unexpected error: $_" -ForegroundColor Red
    }
}

# Test 4: Messages with auth
Write-Host ""
Write-Host "4. Testing /messages WITH auth (should accept)..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $authToken"
        "Content-Type" = "application/json"
    }
    
    $body = @{
        jsonrpc = "2.0"
        id = 1
        method = "tools/call"
        params = @{
            name = "find_products"
            arguments = @{
                query = "test"
            }
        }
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Uri "http://localhost:3000/messages?clientId=test-authenticated" -Method Post -Headers $headers -Body $body
    Write-Host "Success: Message accepted" -ForegroundColor Green
    $response | ConvertTo-Json
}
catch {
    Write-Host "Failed: $_" -ForegroundColor Red
}

# Test 5: Invalid clientId
Write-Host ""
Write-Host "5. Testing /messages without clientId param (should return 400)..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $authToken"
        "Content-Type" = "application/json"
    }
    
    $body = @{
        jsonrpc = "2.0"
        id = 1
        method = "ping"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:3000/messages" -Method Post -Headers $headers -Body $body -ErrorAction Stop
    Write-Host "Failed: Should have returned 400 but got: $($response.StatusCode)" -ForegroundColor Red
}
catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "Success: Correctly returned 400 Bad Request" -ForegroundColor Green
    }
    else {
        Write-Host "Failed: Unexpected error: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
