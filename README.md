
# Robinhood Portfolio Automation

Automated portfolio tracking system that extracts data from Robinhood and exports to Google Sheets.

## Features

- ✅ **Browser Automation** - Uses Selenium to access Robinhood
- ✅ **Complete Data Extraction** - Price, shares, cost basis, dividends, fair value
- ✅ **Auto Calculations** - Diversity %, performance %, gain/loss
- ✅ **Google Sheets Export** - Updates your tracking spreadsheet
- ✅ **Secure** - Encrypted credential storage
- ✅ **Robinhood Gold Support** - Extracts analyst price targets

## Quick Start

### 1. Install Dependencies
```bash
python3 -m venv portfolio_env
source portfolio_env/bin/activate  # On Windows: portfolio_env\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Credentials
```bash
python src/credentials.py setup
```

### 3. Run Portfolio Extraction
```bash
python src/complete_portfolio_system.py
```

## Project Structure
robinhood-automation/
├── src/               # Source code
├── config/            # Configuration files
├── secrets/           # Encrypted credentials (gitignored)
├── data/              # Portfolio data exports
└── logs/              # Application logs
## Configuration

1. Copy `config/config.example.json` to `config/config.json`
2. Add your Google Sheets ID
3. Place Google service account JSON in `config/`

## Security

- Credentials encrypted with Fernet (AES-128)
- Browser session saved locally
- No sensitive data in version control
- Service account for Google Sheets API

## Scheduling

### Weekly Automation (Linux/Mac)
```bash
# Add to crontab
0 18 * * 0 cd /path/to/robinhood-automation && /path/to/portfolio_env/bin/python src/complete_portfolio_system.py
```

### Weekly Automation (Windows)
Use Task Scheduler to run `complete_portfolio_system.py` weekly

## License

MIT License - Free to use and modify

## Disclaimer

This tool is for personal portfolio tracking only. Use at your own risk. Not affiliated with Robinhood.
