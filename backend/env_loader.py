"""Load environment variables from .env file."""
import os
from pathlib import Path


def load_env():
    """Load .env file into environment variables."""
    env_path = Path(__file__).parent.parent / ".env"

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        print(f"📝 Loaded: {key.strip()}")


# Load on import
load_env()
