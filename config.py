import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent   # folder containing config.py (project root)

load_dotenv(BASE_DIR / ".env")


def load_config(path=None):
    if path is None:
        path = BASE_DIR / "config.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_key(config):
    var_name = config["llm"]["api_key_env"]
    api_key = os.environ.get(var_name)
    if not api_key:
        raise RuntimeError(
            f"Environment variable {var_name} is not set. "
            "Set it in Windows or in a .env file."
        )
    return api_key