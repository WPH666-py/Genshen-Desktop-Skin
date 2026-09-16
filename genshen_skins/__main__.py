# -*- coding: utf-8 -*-
"""允许 `python -m genshen_skins ...`。"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
