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

    def should_skip_dir(self,dir_name):
        return dir_name.lower() in self.ignore_dirs

    def should_skip_file(self,file_name):
        name=file_name.lower()
        return any(fnmatch.fnmatchcase(name,pattern) for pattern in self.ignore_files)

if __name__ == "__main__":
    rules = IgnoreRules()
    print("Ignored dirs:", rules.ignore_dirs)
    print("Ignored files:", rules.ignore_files)
    print(rules.should_skip_dir("venv"))        # True
    print(rules.should_skip_dir("src"))         # False
    print(rules.should_skip_file(".ENV"))       # True
    print(rules.should_skip_file("secret.key")) # True
    print(rules.should_skip_file("main.py"))    # False
