@echo off
echo ===================================================
echo  Log Stack Diagnostic Tool
setlocal enabledelayedexpansion

:: Configuration
set GRAFANA_URL=http://localhost:3140
set LOKI_URL=http://localhost:3100
set GRAFANA_USER=admin
set GRAFANA_PASS=windsurf123
set LOKI_HEALTH=%LOKI_URL%/ready
set LOKI_METRICS=%LOKI_URL%/metrics
set LOKI_READY=%LOKI_URL%/ready
set LOKI_RING=%LOKI_URL%/ring
set LOKI_CONFIG_VERSION=%LOKI_URL%/config
set PROMTAIL_METRICS=http://localhost:9080/metrics

:: Simple color indicators
set "RED=[ERROR] "
set "GREEN=[OK] "
set "YELLOW=[WARN] "
set "BLUE=[INFO] "
set "RESET= "

:: Check if running as admin
net session >nul 2>&1
if %ERRORLEVEL% == 0 (
    set IS_ADMIN=1
) else (
    set IS_ADMIN=0
)

echo Checking Docker services...
echo ===================================================

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %RED%ERROR: Docker is not running or not accessible%RESET%
    exit /b 1
) else (
    echo %GREEN%✓ Docker is running%RESET%
)

:: Function to check container status
:check_container
setlocal
set CONTAINER=%~1
set NAME=%~2
set REQUIRED=%~3

for /f "tokens=*" %%i in ('docker ps -a --filter "name=^%CONTAINER%$" --format "{{.Status}}\t{{.Names}}\t{{.Ports}}" 2^>^&1') do (
    echo %%i
    set CONTAINER_INFO=%%i
)

if "!CONTAINER_INFO!"=="" (
    if "%REQUIRED%"=="1" (
        echo %RED%✗ %NAME% container not found%RESET%
        set ERROR=1
    ) else (
        echo %YELLOW%! %NAME% container not found (optional)%RESET%
    )
) else (
    echo %GREEN%✓ %NAME% container found%RESET%
    echo    Status: !CONTAINER_INFO!
)
endlocal & set ERROR=%ERROR%
goto :eof

:: Check required containers
call :check_container "loki" "Loki" "1"
call :check_container "promtail" "Promtail" "1"
call :check_container "grafana" "Grafana" "1"

:: Check container logs for errors
:check_container_logs
setlocal
set CONTAINER=%~1
set NAME=%~2
set MAX_LINES=10

echo.
echo Checking %NAME% logs for errors...
echo ---------------------------------------------------

docker logs --tail %MAX_LINES% %CONTAINER% 2>&1 | findstr /i "error fail exception"
if %ERRORLEVEL% EQU 0 (
    echo %YELLOW%! Found potential issues in %NAME% logs (showing last %MAX_LINES% lines)%RESET%
) else (
    echo %GREEN%✓ No errors found in %NAME% logs (last %MAX_LINES% lines)%RESET%
)
endlocal
goto :eof

call :check_container_logs "loki" "Loki"
call :check_container_logs "promtail" "Promtail"
call :check_container_logs "grafana" "Grafana"

:: Check Loki endpoints
echo.
echo Checking Loki endpoints...
echo ===================================================

:check_endpoint
setlocal
set URL=%~1
set NAME=%~2

powershell -Command "try { $response = Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 5; echo %GREEN%✓ %NAME% (%URL%) - Status: $($response.StatusCode)%RESET% } catch { Write-Host '%RED%✗ %NAME% (%URL%) - Error: $($_.Exception.Message)%RESET%' }"
endlocal
goto :eof

call :check_endpoint "%LOKI_HEALTH%" "Loki Health"
call :check_endpoint "%LOKI_METRICS%" "Loki Metrics"
call :check_endpoint "%LOKI_RING%" "Loki Ring"
call :check_endpoint "%PROMTAIL_METRICS%" "Promtail Metrics"

:: Check Grafana
echo.
echo Checking Grafana...
echo ===================================================

powershell -Command "try { $response = Invoke-WebRequest -Uri '%GRAFANA_URL%/api/health' -UseBasicParsing -TimeoutSec 5; echo %GREEN%✓ Grafana is running%RESET%; $health = $response.Content | ConvertFrom-Json; echo '   Database: ' + $health.database; echo '   Version: ' + $health.version } catch { Write-Host '%RED%✗ Grafana is not accessible: ' + $_.Exception.Message + '%RESET%' }"

:: Check if we can query Loki from Grafana
echo.
echo Checking Loki data source in Grafana...
echo ===================================================

powershell -Command "try { 
    $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(('%{0}:{1}' -f '%GRAFANA_USER%','%GRAFANA_PASS%')));
    $headers = @{ 
        'Authorization' = "Basic $auth"
        'Content-Type' = 'application/json'
    };
    $datasources = Invoke-RestMethod -Uri '%GRAFANA_URL%/api/datasources' -Headers $headers -Method Get -UseBasicParsing;
    $lokiDs = $datasources | Where-Object { $_.type -eq 'loki' } | Select-Object -First 1;
    if ($lokiDs) { 
        Write-Host '%GREEN%✓ Found Loki data source: ' $lokiDs.name ' (ID:' $lokiDs.id ')' '%RESET%';
        Write-Host '   URL:' $lokiDs.url;
        
        # Test Loki query
        $queryUrl = "%GRAFANA_URL%/api/ds/query";
        $query = @{
            queries = @(
                @{
                    refId = 'A';
                    expr = 'count_over_time({job="windsurf"} [5m])';
                    queryType = 'range';
                    datasource = @{ type = 'loki'; uid = $lokiDs.uid };
                    editorMode = 'code';
                    expr = 'count_over_time({job="windsurf"} [5m])';
                }
            );
            from = 'now-1h';
            to = 'now';
        } | ConvertTo-Json -Depth 5;
        
        try {
            $result = Invoke-RestMethod -Uri $queryUrl -Headers $headers -Method Post -Body $query -ContentType 'application/json' -UseBasicParsing;
            $count = $result.results.A.frames[0].data.values[1] | Measure-Object -Sum | Select-Object -ExpandProperty Sum;
            Write-Host ('%GREEN%✓ Loki query successful. Found ' + $count + ' log entries in the last hour%RESET%');
        } catch {
            Write-Host ('%YELLOW%! Loki query failed: ' + $_.Exception.Message + '%RESET%');
        }
    } else { 
        Write-Host '%RED%✗ No Loki data source found in Grafana%RESET%'; 
    }
} catch { 
    Write-Host ('%RED%✗ Failed to check Grafana data sources: ' + $_.Exception.Message + '%RESET%'); 
}"

echo.
echo ===================================================
echo Diagnostic checks completed.
echo ===================================================

if defined ERROR (
    echo.
    echo %RED%Some issues were detected. Check the output above for details.%RESET%
    exit /b 1
) else (
    echo.
    echo %GREEN%All checks passed successfully!%RESET%
    exit /b 0
)
