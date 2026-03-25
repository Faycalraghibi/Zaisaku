#!/usr/bin/env bash
# ──────────────────────────────────────────────
# Zaisaku — Linux/macOS setup script
# ──────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════════"
echo "  Zaisaku — Project Setup"
echo "═══════════════════════════════════════════"
echo ""

# ── 1. Python virtual environment ────────────
echo "→ Creating Python virtual environment..."
python3 -m venv "$PROJECT_ROOT/backend/.venv"
source "$PROJECT_ROOT/backend/.venv/bin/activate"

# ── 2. Install backend dependencies ──────────
echo "→ Installing backend dependencies..."
pip install --upgrade pip
pip install -e "$PROJECT_ROOT/backend[dev]"

# ── 3. Copy .env if needed ───────────────────
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "→ Creating .env from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
else
    echo "→ .env already exists, skipping."
fi

# ── 4. Create test fixtures directory ────────
echo "→ Ensuring test fixtures directory exists..."
mkdir -p "$PROJECT_ROOT/backend/tests/fixtures"

# ── 5. Run unit tests ───────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  Running unit tests..."
echo "═══════════════════════════════════════════"
cd "$PROJECT_ROOT/backend"
pytest tests/unit/ -v --tb=short

echo ""
echo "═══════════════════════════════════════════"
echo "  ✓ Setup complete!"
echo "═══════════════════════════════════════════"
echo ""
echo "  Activate the venv:  source backend/.venv/bin/activate"
echo "  Run tests:          pytest backend/tests/unit/ -v"
echo "  Start backend:      python backend/run.py"
echo ""
