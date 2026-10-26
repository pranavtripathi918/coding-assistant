from pathlib import Path
import os
import hashlib
import pathspec
import logging
import fnmatch

from config import load_config, get_ignore_patterns

logger = logging.getLogger(__name__)

class IgnoreRules:
    def __init__(self, config_path=None):
        self.config = load_config(config_path)
        self.ignore_dirs,self.ignore_files = get_ignore_patterns(self.config)
        self.extensions = self.config["indexing"]["supported_extensions"]
        self.max_file_size = self.config["indexing"]["max_file_size_kb"] * 1024

    def get_extensions(self):
        vals = self.extensions
        vals = [val.lower() for val in vals]
        return vals

    def should_skip_dir(self,dir_name):
        return dir_name.lower() in self.ignore_dirs

    def should_skip_file(self,file_name):
        name=file_name.lower()
        return any(fnmatch.fnmatchcase(name,pattern) for pattern in self.ignore_files)

def scan_project(root):
    rules = IgnoreRules()
    root = Path(root).resolve()
    extensions = rules.get_extensions()
    max_size = rules.max_file_size

    results = []
    for current_folder,subfolders,files in os.walk(root):
        keep = []
        for d in subfolders:
            if not rules.should_skip_dir(d):
                keep.append(d)
        subfolders[:] = keep

        for file in files:
            if rules.should_skip_file(file):
                continue
            path = Path(current_folder)/file
            suffix = path.suffix.lower()

            if not suffix in extensions:
                continue

            try:
               path_size = path.stat().st_size
            except OSError as e:
                logger.warning("Skipped unreadable file: %s (%s)", path, e)
                continue

            if (path_size > max_size):
                logger.info("Skipped (too large): %s (%d bytes)", path, path_size)
                continue

            records = {"relative_path":path.relative_to(root).as_posix(), "extension":suffix, "size":path_size}
            results.append(records)

    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(scan_project("."))
