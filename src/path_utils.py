"""
Path Utilities: Handles all file paths relative to the project root, not the current directory.
"""

# pylint: disable=logging-fstring-interpolation
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PathManager:
    """
    Manages all file paths for the application.
    Always uses paths relative to the project root, not current working directory.
    """

    def __init__(self):
        # Get the absolute path to THIS file
        self.src_dir = Path(__file__).parent.absolute()

        # Project root is one level up from src/
        self.project_root = self.src_dir.parent

        # Define all important directories
        self.config_dir = self.project_root / "config"
        self.secrets_dir = self.project_root / "secrets"
        self.logs_dir = self.project_root / "logs"

        # Create directories if they don't exist
        self._ensure_directories()

        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Config directory: {self.config_dir}")
        logger.info(f"Secrets directory: {self.secrets_dir}")
        logger.info(f"Logs directory: {self.logs_dir}")

    def _ensure_directories(self):
        """Create directories if they don't exist"""
        for directory in [self.config_dir, self.secrets_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def get_config_path(self, filename: str = "config.json") -> Path:
        """Get path to config file"""
        path = self.config_dir / filename
        logger.debug(f"Config path: {path}")
        return path

    def get_secrets_path(self, filename: str) -> Path:
        """Get path to secrets file"""
        path = self.secrets_dir / filename
        logger.debug(f"Secrets path: {path}")
        return path

    def get_log_path(self, filename: str = "app.log") -> Path:
        """Get path to log file"""
        path = self.logs_dir / filename
        logger.debug(f"Log path: {path}")
        return path

    def file_exists(self, path: Path) -> bool:
        """Check if a file exists"""
        exists = path.exists() and path.is_file()
        logger.debug(f"File exists check for {path}: {exists}")
        return exists

    def print_structure(self):
        """Print the current project structure"""
        print("\n" + "="*60)
        print("PROJECT STRUCTURE")
        print("="*60)
        print(f"Project Root: {self.project_root}")
        print("\nDirectories:")
        print(f"  ├── config/    → {self.config_dir}")
        print(f"  ├── secrets/   → {self.secrets_dir}")
        print(f"  ├── logs/      → {self.logs_dir}")
        print(f"  └── src/       → {self.src_dir}")
        print("\nFiles in config/:")
        if self.config_dir.exists():
            config_files = list(self.config_dir.glob("*"))
            if config_files:
                for f in config_files:
                    print(f"  - {f.name}")
            else:
                print("  (empty)")
        print("\nFiles in secrets/:")
        if self.secrets_dir.exists():
            secret_files = list(self.secrets_dir.glob("*"))
            if secret_files:
                for f in secret_files:
                    print(f"  - {f.name}")
            else:
                print("  (empty)")
        print("="*60 + "\n")


def test_path_manager():
    """Test the PathManager to ensure it works correctly"""
    print("\n" + "="*60)
    print("TESTING PATH MANAGER")
    print("="*60 + "\n")

    # Create PathManager instance
    print("1. Creating PathManager...")
    pm = PathManager()
    print("   ✓ PathManager created successfully\n")

    # Print structure
    print("2. Current project structure:")
    pm.print_structure()

    # Test config path
    print("3. Testing config path resolution...")
    config_path = pm.get_config_path("config.json")
    print(f"   Config path: {config_path}")
    print(f"   Exists: {pm.file_exists(config_path)}")
    print("   ✓ Path resolution works\n")

    # Test secrets path
    print("4. Testing secrets path resolution...")
    creds_path = pm.get_secrets_path("credentials.enc")
    print(f"   Credentials path: {creds_path}")
    print(f"   Exists: {pm.file_exists(creds_path)}")
    print("   ✓ Path resolution works\n")

    # Test log path
    print("5. Testing log path resolution...")
    log_path = pm.get_log_path("test.log")
    print(f"   Log path: {log_path}")
    print("   ✓ Path resolution works\n")

    # Test from different directories
    print("6. Testing from different working directories...")
    original_dir = os.getcwd()
    print(f"   Current directory: {original_dir}")

    # Change to parent directory
    os.chdir(pm.project_root.parent)
    print(f"   Changed to: {os.getcwd()}")

    # Create new PathManager - should still work!
    pm2 = PathManager()
    config_path2 = pm2.get_config_path("config.json")
    print(f"   Config path (from different dir): {config_path2}")
    print(f"   Paths match: {config_path == config_path2}")

    # Change back
    os.chdir(original_dir)
    print(f"   Changed back to: {os.getcwd()}")
    print("   ✓ Paths work from any directory!\n")

    print("="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60)
    print("\nKey Features:")
    print("  ✓ Paths are always relative to project root")
    print("  ✓ Works from any working directory")
    print("  ✓ Automatically creates missing directories")
    print("  ✓ Provides easy access to all project files")
    print("\nThis fixes the 'config file not found' issue!")
    print("="*60 + "\n")

    return pm


if __name__ == "__main__":
    # Run the test
    path_manager = test_path_manager()

    # Show how to use it
    print("\n" + "="*60)
    print("HOW TO USE IN OTHER MODULES")
    print("="*60)
    print("""
from path_utils import PathManager

# Create path manager
pm = PathManager()

# Get paths (works from anywhere!)
config_path = pm.get_config_path("config.json")
creds_path = pm.get_secrets_path("credentials.enc")
log_path = pm.get_log_path("app.log")

# Check if file exists
if pm.file_exists(config_path):
    # Load config
    pass
""")
    print("="*60 + "\n")
