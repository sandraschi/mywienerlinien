set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute repo-wide quality checks (Ruff)
lint:
    uv run ruff check .

# Execute repo-wide auto-fixes and formatting (Ruff)
fix:
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    uv run safety check

# ── Project Specific ──────────────────────────────────────────────────────────

# Run the Wiener Linien MCP server
run:
    uv run mywienerlinien

# Serve the web_sota FastAPI backend (fleet-start UvicornTarget: server:app, port 11170)
serve:
    uv run uvicorn server:app --host 127.0.0.1 --port 11170 --app-dir web_sota/backend

# Run the test suite
test:
    uv run pytest tests/ -q

# Format + auto-fix (ruff)
fmt:
    uv run ruff check src/ --fix
    uv run ruff format src/

# First-time dev setup: sync deps + install pre-commit hooks
bootstrap:
    uv sync --extra dev
    uv run pre-commit install

# All gates green: lint + format-check + tests + webapp typecheck + webapp lint
gates-green:
    uv run ruff check src/
    uv run ruff format src/ --check
    uv run pytest tests/ -q
    powershell.exe -NoProfile -Command "npm run check --prefix '{{justfile_directory()}}/web_sota'"
    powershell.exe -NoProfile -Command "npm run biome:ci --prefix '{{justfile_directory()}}/web_sota'"

# CUA browser smoke test for the webapp (pre-Tauri walk)
cua-webapp-test:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/scripts/just/cua-webapp-test.ps1"

# Build the Claude Desktop .mcpb bundle (wipe + fresh-copy src -> mcpb/src inside)
mcpb-pack:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/mcpb/pack.ps1"

# Clean build artifacts
clean:
    @Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @Write-Host "Cleaned."

