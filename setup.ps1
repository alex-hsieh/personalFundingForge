# FundingForge Setup Script (PowerShell)
# This script helps set up the development environment on Windows

Write-Host "🚀 FundingForge Setup" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Node.js
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed. Please install Node.js 20+ first." -ForegroundColor Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
try {
    $null = Get-Command psql -ErrorAction Stop
    Write-Host "✅ PostgreSQL client found" -ForegroundColor Green
} catch {
    Write-Host "⚠️  PostgreSQL client not found. Make sure PostgreSQL is installed and running." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host ""
Write-Host "🐍 Setting up Python virtual environment..." -ForegroundColor Yellow
Set-Location agent-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-Location ..

Write-Host ""
Write-Host "📝 Setting up environment files..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "✅ Created .env (please edit with your credentials)" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env already exists, skipping" -ForegroundColor Yellow
}

if (-not (Test-Path agent-service\.env)) {
    Copy-Item agent-service\.env.example agent-service\.env
    Write-Host "✅ Created agent-service\.env (please edit with your credentials)" -ForegroundColor Green
} else {
    Write-Host "⚠️  agent-service\.env already exists, skipping" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env and agent-service\.env with your AWS credentials"
Write-Host "2. Start PostgreSQL (or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15)"
Write-Host "3. Initialize database: npm run db:push"
Write-Host "4. Start agent service: cd agent-service; .\venv\Scripts\Activate.ps1; python main.py"
Write-Host "5. Start Express backend: npm run dev"
Write-Host "6. Open http://localhost:5000"
Write-Host ""
Write-Host "📚 For more information, see README.md" -ForegroundColor Cyan
