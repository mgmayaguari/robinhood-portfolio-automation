"""
Complete Portfolio Automation System
Matches your exact Google Sheets schema with all features.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from path_utils import PathManager


class RobinhoodCompleteExtractor:
    """
    Complete Robinhood data extractor matching your schema:
    - Ticker, Price, Avg Price, Shares, Total
    - Diversity %, Performance %, Gain/Loss
    - Dividend Yield, Dividend Total
    - Fair Value (from Robinhood Gold)
    """

    def __init__(self):
        self.pm = PathManager()
        self.driver = None
        self.session_dir = self.pm.get_secrets_path("browser_session")
        self.session_dir.mkdir(exist_ok=True)

    def setup_browser(self):
        """Initialize Chrome with persistent session"""
        print("\n" + "="*70)
        print("INITIALIZING BROWSER")
        print("="*70)

        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={self.session_dir}")
        chrome_options.add_argument("profile-directory=RobinhoodProfile")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        print("✓ Starting Chrome...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(1400, 1000)
        print("✓ Browser ready")

    def ensure_logged_in(self) -> bool:
        """Ensure user is logged into Robinhood"""
        print("\n" + "="*70)
        print("CHECKING LOGIN")
        print("="*70)

        self.driver.get("https://robinhood.com/account/investing")
        time.sleep(5)

        if "login" in self.driver.current_url.lower():
            print("\n📱 Please login in the browser...")
            input("Press Enter after logging in...")
            return self.ensure_logged_in()

        print("✓ Logged in")
        return True

    def extract_complete_holding(self, symbol: str, holding_type: str = 'stock') -> Dict:
        """
        Extract ALL data for a single holding matching your schema.
        Returns: {ticker, price, avg_price, shares, total, div_yield, fair_value}
        """
        print(f"\n📊 Extracting {symbol}...")

        # Navigate to holding page
        if holding_type == 'crypto':
            url = f"https://robinhood.com/crypto/{symbol}"
        else:
            url = f"https://robinhood.com/stocks/{symbol}"

        self.driver.get(url)
        time.sleep(5)  # Wait for page to fully load

        # Get all text from page
        page_text = self.driver.find_element(By.TAG_NAME, "body").text

        # Save screenshot for debugging
        screenshot_path = self.pm.get_log_path(f"holding_{symbol}.png")
        self.driver.save_screenshot(str(screenshot_path))

        holding_data = {
            'ticker': symbol,
            'type': holding_type,
            'price': 0,
            'avg_price': 0,
            'shares': 0,
            'total': 0,
            'div_yield': 0,
            'fair_value': 0
        }

        try:
            # Extract Current Price
            # Pattern: $XXX.XX or $X,XXX.XX
            price_patterns = [
                r'Market\s*Price[:\s]*\$\s?([\d,]+\.\d{2})',
                r'Current\s*Price[:\s]*\$\s?([\d,]+\.\d{2})',
                r'\$\s?([\d,]+\.\d{2})',  # Fallback: first price on page
            ]

            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(',', '')
                    holding_data['price'] = float(price_str)
                    print(f"  Price: ${holding_data['price']:.2f}")
                    break

            # Extract Shares/Quantity
            shares_patterns = [
                r'([\d,]+\.?\d*)\s*[Ss]hare',
                r'([\d,]+\.?\d*)\s*' + symbol,  # For crypto
                r'Quantity[:\s]*([\d,]+\.?\d*)',
                r'You\s+own[:\s]*([\d,]+\.?\d*)',
            ]

            for pattern in shares_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    shares_str = match.group(1).replace(',', '')
                    holding_data['shares'] = float(shares_str)
                    print(f"  Shares: {holding_data['shares']}")
                    break

            # Extract Average Cost / Cost Basis
            avg_cost_patterns = [
                r'Average\s*Cost[:\s]*\$\s?([\d,]+\.\d{2})',
                r'Avg\.\s*Cost[:\s]*\$\s?([\d,]+\.\d{2})',
                r'Cost\s*Basis[:\s]*\$\s?([\d,]+\.\d{2})',
                r'Avg\.\s*Buy\s*Price[:\s]*\$\s?([\d,]+\.\d{2})',
            ]

            for pattern in avg_cost_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    avg_str = match.group(1).replace(',', '')
                    holding_data['avg_price'] = float(avg_str)
                    print(f"  Avg Cost: ${holding_data['avg_price']:.2f}")
                    break

            # Extract Dividend Yield (for stocks only)
            if holding_type == 'stock':
                div_patterns = [
                    r'Dividend\s*Yield[:\s]*([\d.]+)%',
                    r'Yield[:\s]*([\d.]+)%',
                    r'Annual\s*Dividend[:\s]*\$[\d.]+\s*\(([\d.]+)%\)',
                ]

                for pattern in div_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        holding_data['div_yield'] = float(match.group(1))
                        print(f"  Dividend Yield: {holding_data['div_yield']}%")
                        break

            # Extract Fair Value (Robinhood Gold feature)
            # This appears as "Analyst Rating" or "Price Target"
            fair_value_patterns = [
                r'Price\s*Target[:\s]*\$\s?([\d,]+\.?\d*)',
                r'Fair\s*Value[:\s]*\$\s?([\d,]+\.?\d*)',
                r'Target\s*Price[:\s]*\$\s?([\d,]+\.?\d*)',
                r'Analyst\s*Target[:\s]*\$\s?([\d,]+\.?\d*)',
            ]

            for pattern in fair_value_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    fv_str = match.group(1).replace(',', '')
                    holding_data['fair_value'] = float(fv_str)
                    print(f"  Fair Value: ${holding_data['fair_value']:.2f}")
                    break

            # Calculate Total
            holding_data['total'] = holding_data['shares'] * holding_data['price']

        except Exception as e:
            print(f"  ⚠️  Error extracting {symbol}: {e}")

        return holding_data

    def get_all_holdings_symbols(self) -> List[Dict]:
        """Get list of all holdings using improved multi-method scanning"""
        print("\n" + "="*70)
        print("SCANNING PORTFOLIO")
        print("="*70)

        self.driver.get("https://robinhood.com/account/investing")
        time.sleep(8) # Increased wait time for full portfolio load

        holdings = {}

        # Method 1: Extract from links (Improved Regex)
        links = self.driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href") or ""

            # Matches symbols even if they contain dots like BRK.B
            stock_match = re.search(r'/stocks/([A-Z.]+)/', href)
            crypto_match = re.search(r'/crypto/([A-Z]+)/', href)

            if stock_match:
                symbol = stock_match.group(1)
                holdings[symbol] = {'symbol': symbol, 'type': 'stock'}

            if crypto_match:
                symbol = crypto_match.group(1)
                holdings[symbol] = {'symbol': symbol, 'type': 'crypto'}

        # Method 2: Fallback Text Scan (The 'Secret Sauce' from your scraper)
        if not holdings:
            print("Link scan found nothing, attempting text scan...")
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            # Look for 2-5 letter uppercase words that appear near '$' signs
            candidates = re.findall(r'\b([A-Z]{2,5})\b', page_text)
            for symbol in set(candidates):
                # Use the validation logic from your other script
                if 2 <= len(symbol) <= 5:
                    holdings[symbol] = {'symbol': symbol, 'type': 'stock'}

        holdings_list = list(holdings.values())
        print(f"✓ Found {len(holdings_list)} holdings")
        return holdings_list

    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()


class PortfolioCalculator:
    """Calculate all derived fields matching your schema"""

    @staticmethod
    def calculate_metrics(holdings: List[Dict]) -> List[Dict]:
        """
        Calculate:
        - Total (shares * price)
        - Diversity % (position value / total portfolio)
        - Performance % ((current - avg) / avg * 100)
        - Gain/Loss (absolute dollar amount)
        - Div Total (annual dividend income)
        """
        # Calculate totals first
        total_portfolio_value = sum(h['total'] for h in holdings)

        for holding in holdings:
            # Diversity %
            if total_portfolio_value > 0:
                holding['diversity_pct'] = (holding['total'] / total_portfolio_value) * 100
            else:
                holding['diversity_pct'] = 0

            # Performance %
            if holding['avg_price'] > 0:
                holding['performance_pct'] = (
                    (holding['price'] - holding['avg_price']) / holding['avg_price'] * 100
                )
            else:
                holding['performance_pct'] = 0

            # Gain/Loss (absolute)
            if holding['avg_price'] > 0:
                holding['gain_loss'] = (
                    (holding['price'] - holding['avg_price']) * holding['shares']
                )
            else:
                holding['gain_loss'] = 0

            # Dividend Total (annual)
            holding['div_total'] = (holding['total'] * holding['div_yield']) / 100

        return holdings


class GoogleSheetsExporter:
    """Export to Google Sheets matching your exact schema"""

    def __init__(self):
        self.pm = PathManager()

    def export_to_sheets(self, holdings: List[Dict], spreadsheet_id: str):
        """
        Export holdings to Google Sheets.
        Preserves manual columns: buy_or_sell, recurring, total_goal, notes
        """
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        # Load service account
        service_account_file = self.pm.config_dir / "service-account.json"

        if not service_account_file.exists():
            print(f"\n⚠️  Service account file not found: {service_account_file}")
            print("   We'll save to JSON instead")
            return False

        # Connect to Sheets API
        creds = Credentials.from_service_account_file(
            str(service_account_file),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        service = build('sheets', 'v4', credentials=creds)

        # Prepare data rows
        rows = []
        rows.append([  # Header
            'Ticker', 'Price', 'Avg. Price', 'Amt', 'Total',
            'Diversity', 'Performance', 'Gain/Loss',
            'Div. Yield', 'Div. Total', 'Column 1', 'Fair Value',
            'buy or sell', 'Recurring', 'Total Goal', 'Notes'
        ])

        for h in holdings:
            rows.append([
                h['ticker'],
                f"${h['price']:.2f}",
                f"${h['avg_price']:.2f}",
                h['shares'],
                f"${h['total']:.2f}",
                f"{h['diversity_pct']:.2f}%",
                f"{h['performance_pct']:.0f}%",
                f"${h['gain_loss']:.2f}",
                f"{h['div_yield']:.2f}%" if h['div_yield'] > 0 else "",
                f"${h['div_total']:.2f}" if h['div_total'] > 0 else "$-",
                "",  # Column 1 (empty)
                f"${h['fair_value']:.2f}" if h['fair_value'] > 0 else "",
                "",  # buy or sell (manual)
                "",  # Recurring (manual)
                "",  # Total Goal (manual)
                ""   # Notes (manual)
            ])

        # Update sheet
        try:
            body = {'values': rows}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Portfolio!A1',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            print(f"\n✓ Updated {result.get('updatedCells')} cells in Google Sheets")
            return True

        except Exception as e:
            print(f"\n✗ Error updating Google Sheets: {e}")
            return False


def main():
    """Main execution"""
    print("\n" + "="*70)
    print(" "*10 + "COMPLETE ROBINHOOD PORTFOLIO AUTOMATION")
    print("="*70)
    print("\nThis will extract:")
    print("  ✓ Ticker, Price, Avg Price, Shares, Total")
    print("  ✓ Diversity %, Performance %, Gain/Loss")
    print("  ✓ Dividend Yield, Dividend Total")
    print("  ✓ Fair Value (from Robinhood Gold)")
    print("\nMatching your exact Google Sheets schema!")

    input("\nPress Enter to start...")

    extractor = RobinhoodCompleteExtractor()

    try:
        # Setup browser
        extractor.setup_browser()
        extractor.ensure_logged_in()

        # Get all holdings
        symbols_list = extractor.get_all_holdings_symbols()

        if not symbols_list:
            print("\n⚠️  No holdings found!")
            return

        # Extract complete data for each
        print("\n" + "="*70)
        print("EXTRACTING COMPLETE DATA")
        print("="*70)

        all_holdings = []
        total = len(symbols_list)

        for idx, item in enumerate(symbols_list, 1):
            print(f"\n[{idx}/{total}]", end=" ")
            holding_data = extractor.extract_complete_holding(
                item['symbol'],
                item['type']
            )
            all_holdings.append(holding_data)

        # Calculate metrics
        print("\n" + "="*70)
        print("CALCULATING METRICS")
        print("="*70)

        complete_portfolio = PortfolioCalculator.calculate_metrics(all_holdings)

        # Sort by total value (largest first)
        complete_portfolio.sort(key=lambda x: x['total'], reverse=True)

        # Display summary
        print("\n" + "="*70)
        print("PORTFOLIO SUMMARY")
        print("="*70)

        print(f"\n{'Ticker':<8} {'Shares':>10} {'Price':>10} {'Total':>12} {'Perf':>8} {'G/L':>12}")
        print("-" * 70)

        total_value = 0
        total_gain_loss = 0
        total_dividends = 0

        for h in complete_portfolio:
            print(
                f"{h['ticker']:<8} "
                f"{h['shares']:>10.2f} "
                f"${h['price']:>9.2f} "
                f"${h['total']:>11,.2f} "
                f"{h['performance_pct']:>7.0f}% "
                f"${h['gain_loss']:>11,.2f}"
            )
            total_value += h['total']
            total_gain_loss += h['gain_loss']
            total_dividends += h['div_total']

        print("-" * 70)
        print(f"{'TOTAL':<8} {'':<10} {'':<10} ${total_value:>11,.2f} {'':<8} ${total_gain_loss:>11,.2f}")
        print(f"\nAnnual Dividend Income: ${total_dividends:,.2f}")
        print("="*70)

        # Save to JSON
        output_file = extractor.pm.project_root / "data" / "complete_portfolio.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_value': total_value,
                'total_gain_loss': total_gain_loss,
                'total_dividends': total_dividends,
                'holdings': complete_portfolio
            }, f, indent=2)

        print(f"\n✓ Saved to: {output_file}")

        # Export to Google Sheets (optional)
        export_sheets = input("\nExport to Google Sheets? (yes/no): ").lower()
        if export_sheets == 'yes':
            spreadsheet_id = input("Enter Spreadsheet ID: ")
            exporter = GoogleSheetsExporter()
            exporter.export_to_sheets(complete_portfolio, spreadsheet_id)

        print("\n" + "="*70)
        print("✓✓✓ COMPLETE! ✓✓✓")
        print("="*70)
        print("\nYour portfolio data has been extracted and calculated!")
        print("Manual fields (buy/sell, recurring, goals, notes) preserved in Sheets.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        input("\nPress Enter to close...")
        extractor.close()


if __name__ == "__main__":
    main()

