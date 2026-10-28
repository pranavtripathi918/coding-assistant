from pathlib import Path
import logging

from indexing.scanner import IgnoreRules

logger = logging.getLogger(__name__)

rules = IgnoreRules()

#This function returns the resolved path if the path is inside the root and not ignored
#Otherwise logs the reason and returns None
def _resolve_safe(root,relative_path):
    root = Path(root).resolve()
    full_path = (root / relative_path).resolve()

    try:
        rel = full_path.relative_to(root)
    except ValueError:
        logger.warning("Path is outside the project: %s", relative_path)
        return None
    if rules.should_skip_file(full_path.name):
        logger.warning("skipped ignore files: %s",rel)
        return None

    for part in rel.parts[:-1]:
        if rules.should_skip_dir(part):
            logger.warning("skipped ignore folder '%s':%s",part,rel)
            return None

    return full_path

#This function reads file content and returns text or None if file can't or shouldn't be read
def read_file(root,relative_path):
    full_path = _resolve_safe(root, relative_path)
    if full_path is None:
        return None

    try:
        return full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("Not valid UTF-8, skipped: %s", relative_path)
        return None
    except OSError as e:
        logger.warning("Could not read %s (%s)", relative_path, e)
        return None

def write_file():
    pass

def backup_file():
    pass
