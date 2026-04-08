
#!/bin/bash

echo "=================================="
echo "Robinhood Portfolio Automation Setup"
echo "=================================="

# Check Python version
python3 --version || { echo "Python 3 not found!"; exit 1; }

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv portfolio_env

# Activate
source portfolio_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p config data logs secrets

# Create directory markers
touch data/.gitkeep
touch logs/.gitkeep
touch secrets/.gitkeep

# Copy config template
if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "✓ Created config/config.json - Please edit with your settings"
fi

echo ""
echo "=================================="
echo "✓ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Edit config/config.json with your settings"
echo "  2. Run: python src/credentials.py setup"
echo "  3. Run: python src/complete_portfolio_system.py"
echo ""
