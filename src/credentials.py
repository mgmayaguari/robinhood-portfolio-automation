"""
Secure Credential Manager: Encrypts and stores Robinhood credentials safely.
"""

# pylint: disable=logging-fstring-interpolation
# pylint: disable=import-error

import json
import logging
from cryptography.fernet import Fernet, InvalidToken
from path_utils import PathManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class CredentialManager:
    """
    Manages encrypted storage of Robinhood credentials.
    Uses Fernet (symmetric encryption) for security.
    """

    def __init__(self):
        self.pm = PathManager()
        self.key_file = self.pm.get_secrets_path("encryption.key")
        self.creds_file = self.pm.get_secrets_path("credentials.enc")
        self.cipher = None

        logger.info("CredentialManager initialized")
        logger.info(f"Key file: {self.key_file}")
        logger.info(f"Credentials file: {self.creds_file}")

    def _generate_key(self) -> bytes:
        """Generate a new encryption key"""
        key = Fernet.generate_key()
        logger.info("Generated new encryption key")
        return key

    def _save_key(self, key: bytes):
        """Save encryption key to file"""
        with open(self.key_file, 'wb') as f:
            f.write(key)

        # Set restrictive permissions (Unix only)
        try:
            self.key_file.chmod(0o600)  # Read/write for owner only
            logger.info(f"Set permissions to 600 on {self.key_file}")
        except PermissionError as e:
            logger.warning(f"Could not set file permissions: {e}")

        logger.info(f"Encryption key saved to {self.key_file}")

    def _load_key(self) -> bytes:
        """Load encryption key from file"""
        if not self.pm.file_exists(self.key_file):
            raise FileNotFoundError(
                f"Encryption key not found at {self.key_file}. "
                "Run setup first."
            )

        with open(self.key_file, 'rb') as f:
            key = f.read()

        logger.info("Encryption key loaded")
        return key

    def _get_cipher(self) -> Fernet:
        """Get or create cipher for encryption/decryption"""
        if self.cipher is None:
            if self.pm.file_exists(self.key_file):
                key = self._load_key()
            else:
                key = self._generate_key()
                self._save_key(key)

            self.cipher = Fernet(key)
            logger.info("Cipher initialized")

        return self.cipher

    def save_credentials(self, username: str, password: str, totp_secret: str = None):
        """
        Encrypt and save Robinhood credentials.

        Args:
            username: Robinhood email/username
            password: Robinhood password
            totp_secret: Optional TOTP secret for 2FA
        """
        logger.info("Saving credentials...")

        # Create credentials dictionary
        credentials = {
            'username': username,
            'password': password,
        }

        if totp_secret:
            credentials['totp_secret'] = totp_secret
            logger.info("Including 2FA TOTP secret")

        # Convert to JSON
        json_data = json.dumps(credentials).encode('utf-8')

        # Encrypt
        cipher = self._get_cipher()
        encrypted_data = cipher.encrypt(json_data)

        # Save to file
        with open(self.creds_file, 'wb') as f:
            f.write(encrypted_data)

        # Set restrictive permissions
        try:
            self.creds_file.chmod(0o600)
            logger.info(f"Set permissions to 600 on {self.creds_file}")
        except PermissionError as e:
            logger.warning(f"Could not set file permissions: {e}")

        logger.info(f"✓ Credentials encrypted and saved to {self.creds_file}")
        print("\n✓ Credentials saved securely!")
        print(f"  Location: {self.creds_file}")
        print("  Encryption: Fernet (AES-128)")

    def load_credentials(self) -> dict:
        """
        Load and decrypt Robinhood credentials.

        Returns:
            dict: {'username': str, 'password': str, 'totp_secret': str (optional)}
        """
        logger.info("Loading credentials...")

        if not self.pm.file_exists(self.creds_file):
            raise FileNotFoundError(
                f"Credentials not found at {self.creds_file}. "
                "Run setup_credentials() first."
            )

        # Read encrypted data
        with open(self.creds_file, 'rb') as f:
            encrypted_data = f.read()

        # Decrypt
        cipher = self._get_cipher()
        try:
            decrypted_data = cipher.decrypt(encrypted_data)
        except InvalidToken as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError(
                "Failed to decrypt credentials. "
                "The encryption key may be corrupted. "
                "You may need to run setup again."
            ) from e

        # Parse JSON
        credentials = json.loads(decrypted_data.decode('utf-8'))

        logger.info("✓ Credentials loaded and decrypted successfully")
        logger.info(f"  Username: {credentials.get('username', 'N/A')}")
        logger.info(f"  Has 2FA: {'totp_secret' in credentials}")

        return credentials

    def credentials_exist(self) -> bool:
        """Check if credentials are already saved"""
        exists = self.pm.file_exists(self.creds_file)
        logger.info(f"Credentials exist: {exists}")
        return exists

    def delete_credentials(self):
        """Delete saved credentials (for re-setup)"""
        if self.pm.file_exists(self.creds_file):
            self.creds_file.unlink()
            logger.info("Credentials deleted")
            print("✓ Credentials deleted")

        if self.pm.file_exists(self.key_file):
            self.key_file.unlink()
            logger.info("Encryption key deleted")
            print("✓ Encryption key deleted")


def setup_credentials():
    """
    Interactive setup for Robinhood credentials.
    This is what users run the first time.
    """
    print("\n" + "="*60)
    print("ROBINHOOD CREDENTIAL SETUP")
    print("="*60 + "\n")

    cm = CredentialManager()

    # Check if credentials already exist
    if cm.credentials_exist():
        print("⚠️  Credentials already exist!")
        overwrite = input("Do you want to overwrite them? (yes/no): ").lower()
        if overwrite != 'yes':
            print("Setup cancelled.")
            return
        cm.delete_credentials()
        print()

    # Get credentials from user
    print("Enter your Robinhood credentials:")
    print("(These will be encrypted and stored locally)\n")

    username = input("Email/Username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return

    password = input("Password: ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        return

    # Ask about 2FA
    print("\n" + "-"*60)
    print("TWO-FACTOR AUTHENTICATION (2FA)")
    print("-"*60)
    print("If you have 2FA enabled on Robinhood, you need your TOTP secret.")
    print("\nHow to get your TOTP secret:")
    print("  1. Go to Robinhood app/web → Settings → Security")
    print("  2. Enable 2FA (if not already enabled)")
    print("  3. When shown the QR code, look for 'Can't scan?' or 'Enter manually'")
    print("  4. Copy the secret key (it's a long string of letters/numbers)")
    print()

    use_2fa = input("Do you use 2FA? (yes/no): ").lower().strip()
    totp_secret = None

    if use_2fa == 'yes':
        totp_secret = input("Enter your TOTP secret: ").strip()
        if not totp_secret:
            print("⚠️  No TOTP secret provided. 2FA will not work.")
            totp_secret = None

    # Save credentials
    print("\n" + "-"*60)
    print("Encrypting and saving credentials...")
    print("-"*60)

    try:
        cm.save_credentials(username, password, totp_secret)
        print("\n" + "="*60)
        print("✓ SETUP COMPLETE!")
        print("="*60)
        print("\nYour credentials are now stored securely.")
        print("You can now use the application.\n")

    except (IOError, PermissionError, ValueError) as e:
        print(f"\n❌ Error saving credentials: {e}")
        logger.error(f"Setup failed: {e}", exc_info=True)


def test_credentials():
    """
    Test loading credentials (without actually using them).
    This verifies encryption/decryption works.
    """
    print("\n" + "="*60)
    print("TESTING CREDENTIAL LOADING")
    print("="*60 + "\n")

    cm = CredentialManager()

    # Check if credentials exist
    if not cm.credentials_exist():
        print("❌ No credentials found!")
        print("Run: python src/credentials.py setup")
        return False

    # Try to load
    try:
        print("Attempting to load and decrypt credentials...")
        creds = cm.load_credentials()

        print("\n✓ Successfully loaded credentials!")
        print("\nCredential Details:")
        print(f"  Username: {creds['username']}")
        print(f"  Password: {'*' * len(creds['password'])} ({len(creds['password'])} characters)")

        if 'totp_secret' in creds:
            secret_len = len(creds['totp_secret'])
            masked_secret = '*' * secret_len
            print(f"  2FA Secret: {masked_secret} ({secret_len} characters)")
            print("  2FA Enabled: ✓ Yes")
        else:
            print("  2FA Enabled: ✗ No")

        print("\n" + "="*60)
        print("✓ CREDENTIAL TEST PASSED!")
        print("="*60 + "\n")

        return True

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Failed to load credentials: {e}")
        logger.error(f"Credential test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import sys

    # Command line interface
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "setup":
            setup_credentials()
        elif command == "test":
            test_credentials()
        elif command == "delete":
            cred_manager = CredentialManager()
            confirm = input("Are you sure you want to delete credentials? (yes/no): ")
            if confirm.lower() == 'yes':
                cred_manager.delete_credentials()
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  setup  - Set up credentials")
            print("  test   - Test loading credentials")
            print("  delete - Delete saved credentials")
    else:
        # No arguments - show menu
        print("\n" + "="*60)
        print("CREDENTIAL MANAGER")
        print("="*60)
        print("\nCommands:")
        print("  python src/credentials.py setup   - Set up credentials")
        print("  python src/credentials.py test    - Test loading credentials")
        print("  python src/credentials.py delete  - Delete credentials")
        print("\n" + "="*60 + "\n")
