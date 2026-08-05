#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["shellcheck-py==0.11.0.1"]
# ///

import os
import sys

os.execvp("shellcheck", ["shellcheck", *sys.argv[1:]])
