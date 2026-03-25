# ──────────────────────────────────────────────
# Zaisaku — Windows setup script
# ──────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Zaisaku — Project Setup"                   -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1. Python virtual environment ────────────
Write-Host "→ Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv "$ProjectRoot\backend\.venv"
& "$ProjectRoot\backend\.venv\Scripts\Activate.ps1"

# ── 2. Install backend dependencies ──────────
Write-Host "→ Installing backend dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -e "$ProjectRoot\backend[dev]"

# ── 3. Copy .env if needed ───────────────────
if (!(Test-Path "$ProjectRoot\.env")) {
    Write-Host "→ Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item "$ProjectRoot\.env.example" "$ProjectRoot\.env"
} else {
    Write-Host "→ .env already exists, skipping." -ForegroundColor Gray
}

# ── 4. Create test fixtures directory ────────
Write-Host "→ Ensuring test fixtures directory exists..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$ProjectRoot\backend\tests\fixtures" | Out-Null

# ── 5. Run unit tests ───────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Running unit tests..."                      -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan

Push-Location "$ProjectRoot\backend"
pytest tests/unit/ -v --tb=short
Pop-Location

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ Setup complete!"                          -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Activate the venv:  backend\.venv\Scripts\Activate.ps1"
Write-Host "  Run tests:          pytest backend/tests/unit/ -v"
Write-Host "  Start backend:      python backend/run.py"
Write-Host ""
