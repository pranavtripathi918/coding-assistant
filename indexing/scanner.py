from pathlib import Path
import os
import hashlib
import pathspec
import logging
import fnmatch

from config import load_config, get_ignore_patterns

class IgnoreRules:
    def __init__(self, config_path=None):
        self.config = load_config(config_path)
        self.ignore_dirs,self.ignore_files = get_ignore_patterns(self.config)
        self.extensions = self.config["indexing"]["supported_extensions"]

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

    for current_folder,subfolders,files in os.walk(root):
        keep = []
        for d in subfolders:
            if not rules.should_skip_dir(d):
                keep.append(d)
        subfolders[:] = keep

        for file in files:
            if rules.should_skip_file(file):
                continue
            print(file)
            print(Path(current_folder)/file)

if __name__ == "__main__":
    scan_project(".")
