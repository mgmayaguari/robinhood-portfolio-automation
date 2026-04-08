"""
Step 5: Refined Robinhood Browser Scraper
Improved extraction with better filtering and data collection.
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
from typing import List, Dict
from path_utils import PathManager


class RobinhoodScraper:
    """Refined Robinhood portfolio scraper"""

    # Known common stocks/ETFs to validate against
    KNOWN_TICKERS = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
        'AMD', 'NFLX', 'DIS', 'BA', 'GE', 'F', 'GM', 'T', 'VZ', 'JPM',
        'BAC', 'WFC', 'C', 'GS', 'MS', 'V', 'MA', 'PYPL', 'SQ', 'SHOP',
        'KO', 'PEP', 'MCD', 'SBUX', 'NKE', 'HD', 'LOW', 'WMT', 'TGT',
        'COST', 'CVS', 'WBA', 'UNH', 'ABBV', 'JNJ', 'PFE', 'MRK',
        'XOM', 'CVX', 'COP', 'SLB', 'HAL', 'OXY', 'MPC', 'VLO',
        'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'VEA', 'VWO',
        'BND', 'AGG', 'TLT', 'GLD', 'SLV', 'USO', 'UNG',
        'ARKK', 'ARKG', 'ARKF', 'ARKW', 'ARKQ',
        'BRK.A', 'BRK.B', 'BLK', 'PLTR', 'COIN', 'RBLX',
        # Add more as needed
        'SPYD', 'JNUG', 'SILJ', 'SMH', 'XLE', 'XLF', 'XLK', 'XLV',
        'LUV', 'DAL', 'AAL', 'UAL', 'BX', 'KKR', 'APO',
        'CL', 'PG', 'UL', 'CLX', 'CHD',
        'WM', 'RSG', 'DRIP'  # Added your holdings
    }

    # Words to exclude (not stock symbols)
    EXCLUDE_WORDS = {
        'USD', 'AM', 'PM', 'OK', 'ID', 'US', 'NEW', 'ETF', 'THE',
        'AND', 'FOR', 'NOT', 'YOU', 'ARE', 'CAN', 'GET', 'SET',
        'ALL', 'NOW', 'TOP', 'HOW', 'WHY', 'WHO', 'WHAT', 'WHEN',
        'GOOD', 'BAD', 'APY', 'API', 'FAQ', 'CEO', 'CFO', 'IPO',
        'SPDR'  # This is actually part of "SPDR S&P" not a symbol
    }

    def __init__(self):
        self.pm = PathManager()
        self.driver = None
        self.session_dir = self.pm.get_secrets_path("browser_session")
        self.session_dir.mkdir(exist_ok=True)

    def setup_browser(self):
        """Initialize Chrome"""
        print("\n" + "="*70)
        print("INITIALIZING BROWSER")
        print("="*70)

        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={self.session_dir}")
        chrome_options.add_argument("profile-directory=RobinhoodProfile")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        print("✓ Starting Chrome...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(1400, 900)
        print("✓ Browser ready")

    def ensure_logged_in(self) -> bool:
        """Check if logged in, otherwise prompt"""
        print("\n" + "="*70)
        print("CHECKING LOGIN STATUS")
        print("="*70)

        self.driver.get("https://robinhood.com/account/investing")
        time.sleep(5)

        current_url = self.driver.current_url
        print(f"Current URL: {current_url}")

        if "login" in current_url.lower():
            print("\n✗ Not logged in")
            print("\n📱 Please login in the browser window...")
            print("   Press Enter after you're on the portfolio page")
            input()
            return self.ensure_logged_in()

        print("✓ Logged in")
        return True

    def extract_holdings_from_page(self) -> List[Dict]:
        """Extract holdings using multiple methods with better filtering"""
        print("\n" + "="*70)
        print("EXTRACTING HOLDINGS")
        print("="*70)

        # Navigate to investing page
        print("\nNavigating to Investing page...")
        self.driver.get("https://robinhood.com/account/investing")
        time.sleep(6)

        # Save screenshot
        screenshot = self.pm.get_log_path("portfolio_page.png")
        self.driver.save_screenshot(str(screenshot))
        print(f"✓ Screenshot: {screenshot}")

        holdings = {}  # Use dict to deduplicate

        # Method 1: Find all stock/crypto links
        print("\n[Method 1] Extracting from links...")
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href") or ""

                # Match /stocks/SYMBOL or /crypto/SYMBOL
                stock_match = re.search(r'/stocks/([A-Z.]+)/', href)
                crypto_match = re.search(r'/crypto/([A-Z]+)/', href)

                if stock_match:
                    symbol = stock_match.group(1)
                    if self._is_valid_symbol(symbol):
                        holdings[symbol] = {'symbol': symbol, 'type': 'stock'}
                        print(f"  ✓ {symbol}")

                if crypto_match:
                    symbol = crypto_match.group(1)
                    holdings[symbol] = {'symbol': symbol, 'type': 'crypto'}
                    print(f"  ✓ {symbol} (crypto)")
        except Exception as e:
            print(f"  ✗ Error: {e}")

        # Method 2: Scan page text for symbols (with strict validation)
        if len(holdings) == 0:
            print("\n[Method 2] Scanning page text...")
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text

                # Find 2-5 letter uppercase words
                candidates = re.findall(r'\b([A-Z]{2,5})\b', page_text)

                for symbol in set(candidates):
                    if self._is_valid_symbol(symbol) and symbol not in holdings:
                        holdings[symbol] = {'symbol': symbol, 'type': 'stock'}
                        print(f"  ? {symbol}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

        print(f"\n✓ Found {len(holdings)} unique holdings")
        return list(holdings.values())

    def _is_valid_symbol(self, symbol: str) -> bool:
        """Validate if string is likely a real stock symbol"""
        if not symbol:
            return False

        # Remove dots (for BRK.B, etc.)
        clean_symbol = symbol.replace('.', '')

        # Exclude known non-symbols
        if clean_symbol in self.EXCLUDE_WORDS:
            return False

        # Length check
        if len(clean_symbol) < 1 or len(clean_symbol) > 5:
            return False

        # Must be all letters (plus dots)
        if not re.match(r'^[A-Z.]+$', symbol):
            return False

        # If it's in our known list, it's valid
        if symbol in self.KNOWN_TICKERS or clean_symbol in self.KNOWN_TICKERS:
            return True

        # Otherwise, be conservative - only accept if 2-4 chars
        # (Most stocks are 3-4 letters, 5-letter symbols are rare)
        if 2 <= len(clean_symbol) <= 4:
            return True

        return False

    def get_holding_details(self, holdings: List[Dict]) -> List[Dict]:
        """Visit each holding page to get quantity and price"""
        print("\n" + "="*70)
        print("FETCHING DETAILED DATA")
        print("="*70)

        detailed = []
        total = len(holdings)

        for idx, holding in enumerate(holdings, 1):
            symbol = holding['symbol']
            holding_type = holding.get('type', 'stock')

            print(f"\n[{idx}/{total}] Processing {symbol}...")

            try:
                # Navigate to the holding page
                if holding_type == 'crypto':
                    url = f"https://robinhood.com/crypto/{symbol}"
                else:
                    url = f"https://robinhood.com/stocks/{symbol}"

                self.driver.get(url)
                time.sleep(4)  # Wait for page load

                # Get page text
                page_text = self.driver.find_element(By.TAG_NAME, "body").text

                # Extract shares/quantity
                # Look for patterns like "10.5 Shares" or "0.5 BTC"
                shares_patterns = [
                    r'([\d,]+\.?\d*)\s*[Ss]hare',
                    r'([\d,]+\.?\d*)\s*' + symbol,  # For crypto like "0.5 BTC"
                ]

                quantity = 0
                for pattern in shares_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        qty_str = match.group(1).replace(',', '')
                        quantity = float(qty_str)
                        print(f"  Quantity: {quantity}")
                        break

                # Extract current price
                # Look for patterns like "$175.50" or "$1,234.56"
                price_pattern = r'\$\s?([\d,]+\.\d{2})'
                price_matches = re.findall(price_pattern, page_text)

                current_price = 0
                if price_matches:
                    # Usually the first price on the page is the current price
                    price_str = price_matches[0].replace(',', '')
                    current_price = float(price_str)
                    print(f"  Price: ${current_price}")

                # Extract average cost if visible
                avg_cost = 0
                avg_patterns = [
                    r'[Aa]verage\s*[Cc]ost[:\s]*\$\s?([\d,]+\.\d{2})',
                    r'[Aa]vg\.\s*[Cc]ost[:\s]*\$\s?([\d,]+\.\d{2})',
                ]

                for pattern in avg_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        cost_str = match.group(1).replace(',', '')
                        avg_cost = float(cost_str)
                        print(f"  Avg Cost: ${avg_cost}")
                        break

                detailed.append({
                    'symbol': symbol,
                    'type': holding_type,
                    'quantity': quantity,
                    'current_price': current_price,
                    'avg_cost': avg_cost
                })

            except Exception as e:
                print(f"  ✗ Error: {e}")
                detailed.append({
                    'symbol': symbol,
                    'type': holding_type,
                    'quantity': 0,
                    'current_price': 0,
                    'avg_cost': 0
                })

        return detailed

    def save_to_json(self, holdings: List[Dict], filename: str = "robinhood_portfolio.json"):
        """Save holdings to JSON"""
        output_path = self.pm.project_root / "data" / filename
        output_path.parent.mkdir(exist_ok=True)

        data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'holdings_count': len(holdings),
            'holdings': holdings
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Saved to: {output_path}")
        return output_path

    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()


def main():
    """Main execution"""
    print("\n" + "="*70)
    print(" "*15 + "ROBINHOOD PORTFOLIO SCRAPER")
    print("="*70)

    scraper = RobinhoodScraper()

    try:
        # Setup
        scraper.setup_browser()

        # Ensure logged in
        if not scraper.ensure_logged_in():
            print("\n❌ Please login and try again")
            return

        # Extract holdings list
        holdings = scraper.extract_holdings_from_page()

        if not holdings:
            print("\n⚠️  No holdings found!")
            print("\nCheck the screenshot and make sure you're on the portfolio page")
            return

        # Show what we found
        print("\n" + "="*70)
        print("HOLDINGS SUMMARY")
        print("="*70)
        print(f"\nFound {len(holdings)} holdings:")
        for h in holdings:
            print(f"  • {h['symbol']} ({h.get('type', 'stock')})")

        # Ask if user wants detailed data
        print("\n" + "-"*70)
        fetch_details = input("Fetch quantities and prices for each? (yes/no): ").lower()

        if fetch_details == 'yes':
            detailed_holdings = scraper.get_holding_details(holdings)
            scraper.save_to_json(detailed_holdings)

            # Display summary
            print("\n" + "="*70)
            print("PORTFOLIO SUMMARY")
            print("="*70)
            print(f"\n{'Symbol':<10} {'Quantity':>12} {'Price':>12} {'Value':>14}")
            print("-" * 70)

            total_value = 0
            for h in detailed_holdings:
                value = h['quantity'] * h['current_price']
                total_value += value
                print(
                    f"{h['symbol']:<10} "
                    f"{h['quantity']:>12.4f} "
                    f"${h['current_price']:>11.2f} "
                    f"${value:>13,.2f}"
                )

            print("-" * 70)
            print(f"{'TOTAL':<10} {'':<12} {'':<12} ${total_value:>13,.2f}")
            print("="*70)
        else:
            scraper.save_to_json(holdings, "robinhood_symbols_only.json")

        print("\n" + "="*70)
        print("✓✓✓ SUCCESS ✓✓✓")
        print("="*70)
        print("\nNext steps:")
        print("  1. ✅ Browser automation working")
        print("  2. 📊 Add yfinance for missing prices")
        print("  3. 📈 Calculate portfolio metrics")
        print("  4. 📤 Export to Google Sheets")
        print("  5. ⏰ Automate weekly runs")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        input("\nPress Enter to close browser...")
        scraper.close()


if __name__ == "__main__":
    main()

