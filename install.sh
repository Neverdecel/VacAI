#!/bin/bash

# VACAI Installation Script

echo "🚀 Installing VACAI dependencies..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Install pip if needed
python3 -m ensurepip --upgrade 2>/dev/null || true

# Install dependencies
python3 -m pip install --user -r requirements.txt

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Make sure .env has your OPENAI_API_KEY"
echo "  2. Run: python3 main.py init --resume resume/your_resume.pdf"
echo "  3. Run: python3 main.py scan"
echo "  4. Run: python3 main.py report"
