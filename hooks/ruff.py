#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["ruff==0.16.1"]
# ///

import os
import sys

os.execvp("ruff", ["ruff", *sys.argv[1:]])
