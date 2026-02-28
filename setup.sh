#!/bin/bash

# FundingForge Setup Script
# This script helps set up the development environment

set -e

echo "🚀 FundingForge Setup"
echo "===================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20+ first."
    exit 1
fi
echo "✅ Node.js $(node --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi
echo "✅ Python $(python3 --version)"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Make sure PostgreSQL is installed and running."
else
    echo "✅ PostgreSQL client found"
fi

echo ""
echo "📦 Installing Node.js dependencies..."
npm install

echo ""
echo "🐍 Setting up Python virtual environment..."
cd agent-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo ""
echo "📝 Setting up environment files..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env (please edit with your credentials)"
else
    echo "⚠️  .env already exists, skipping"
fi

if [ ! -f agent-service/.env ]; then
    cp agent-service/.env.example agent-service/.env
    echo "✅ Created agent-service/.env (please edit with your credentials)"
else
    echo "⚠️  agent-service/.env already exists, skipping"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env and agent-service/.env with your AWS credentials"
echo "2. Start PostgreSQL (or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15)"
echo "3. Initialize database: npm run db:push"
echo "4. Start agent service: cd agent-service && source venv/bin/activate && python main.py"
echo "5. Start Express backend: npm run dev"
echo "6. Open http://localhost:5000"
echo ""
echo "📚 For more information, see README.md"
