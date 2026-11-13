import tempfile
from pathlib import Path
import logging
from difflib import unified_diff
from datetime import datetime
import os
import shutil

from indexing.scanner import IgnoreRules

logger = logging.getLogger(__name__)

class FileWriteError(Exception):
    """Raised when a write or backup is refused or fails."""

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

#This function creates two mutli line string and return a single string representing unified differece between them
def make_diff(old, new, name="file"):
    diff = unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"a/{name}",
        tofile=f"b/{name}",
        lineterm="",
    )
    return "\n".join(diff)

#This function gets the bacckup of the file which meant to be changed
def backup_file(root,relative_path,backup_dir):
    full_path = _resolve_safe(root, relative_path)
    if full_path is None:
        raise FileWriteError(f"Backup refused: {relative_path}")
    if not full_path.is_file():
        raise FileWriteError(f"Backup refused, not a file: {relative_path}")

    root = Path(root).resolve()
    backup_root=(root / backup_dir).resolve()

    try:
        backup_root.relative_to(root)
    except ValueError:
        raise FileWriteError("backup_dir is outside the project")

    rel = full_path.relative_to(root)
    dest_dir = backup_root/rel.parent
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dest = dest_dir / f"{rel.name}.{stamp}.bak"

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{rel.name}.{stamp}-{counter}.bak"
            counter += 1
        shutil.copy2(full_path, dest)
    except OSError as e:
        raise FileWriteError(f"Backup failed for {rel}:{e}") from e
    if not dest.is_file() or dest.stat().st_size != full_path.stat().st_size:
        raise FileWriteError(f"Backup verification failed for {rel}")

    logger.info("Backed up %s to %s", rel, dest)
    return dest

#This function takes LLM suggestion and write the file this work only when it is allowed
def write_file(root,relative_path,content,confirm,setting):
    require_confirmation, backup_before_write, backup_dir = setting

    full_path = _resolve_safe(root, relative_path)
    if full_path is None:
        raise FileWriteError(f"Path not allowed: {relative_path}")

    if not full_path.is_file():
        raise FileWriteError(f"Not an existing file: {relative_path}")

    if require_confirmation and not confirm:
        raise FileWriteError("Confirmation required before writing")

    old = read_file(root, relative_path)
    if old is None:
        raise FileWriteError(f"Cannot read current file: {relative_path}")

    content = content.replace("\r\n", "\n")
    if old == content:
        raise FileWriteError("New content is the same as the old content")

    # Keep the file's original line endings
    uses_crlf = b"\r\n" in full_path.read_bytes()
    text = content.replace("\n","\r\n") if uses_crlf else content

    #no backup path, no write
    backup_path = None
    if backup_before_write:
        backup_path = backup_file(root,relative_path,backup_dir)

    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",encoding="utf-8",newline="",
            dir=full_path.parent,suffix=".tmp",delete=False
        ) as tmp:
            tmp_name = tmp.name
            tmp.write(text)
        os.replace(tmp_name,full_path)
    except OSError as e:
        if tmp_name is not None:
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise FileWriteError(f"Write failed for {relative_path}: {e}") from e

    logger.info("Wrote %s", relative_path)
    return backup_path
