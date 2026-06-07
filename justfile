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

# Clean build artifacts
clean:
    @Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @Write-Host "Cleaned."

