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

def get_ignore_patterns(config):
    idx = config["indexing"]
    ignore_dirs = {d.lower() for d in idx["ignore_dirs"]}
    ignore_files = [f.lower() for f in idx["ignore_files"]]
    return ignore_dirs, ignore_files

def get_chunk(config):
    max_chunk_chars = config["chunking"]["max_chunk_chars"]
    overlap_chars = config["chunking"]["overlap_chars"]

    if not (isinstance(max_chunk_chars, int)):
        raise TypeError("max_chunk_chars should always be an integer")

    if not (isinstance(overlap_chars, int)):
        raise TypeError("overlap_chars should always be an integer")

    if max_chunk_chars <= overlap_chars:
        raise ValueError("max_chunk_chars should be larger than overlap_chars")

    if overlap_chars < 0:
        raise ValueError("overlap_chars should be a positive integer")

    return max_chunk_chars, overlap_chars

def get_safety_setting(config):
    require_confirmation = config["safety"]["require_confirmation"]
    backup_before_write = config["safety"]["backup_before_write"]
    backup_dir = config["safety"]["backup_dir"]

    if not isinstance(require_confirmation, bool):
        raise TypeError("require_confirmation should be a boolean")
    if not isinstance(backup_before_write, bool):
        raise TypeError("backup_before_write should be a boolean")
    if not isinstance(backup_dir, str) or not backup_dir.strip:
        raise ValueError("backup_dir should be a non-empty string")

    return require_confirmation, backup_before_write, backup_dir

def get_embedder(config):
    model = config["embedding"]["model"]
    return model
