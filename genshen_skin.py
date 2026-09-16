# -*- coding: utf-8 -*-
"""`python -m genshen_skin` 的入口（下划线单数形式）。

有人会凭直觉敲 `python -m genshen_skin`（单数、下划线），这个文件让它也能用，
避免 "No module named 'genshen_skin'" 这种本可以避免的挫败。

等价写法共四种：
    genshen-skin list                # 控制台命令（别名 gss）
    python -m genshen-skin list      # genshen-skin.py
    python -m genshen_skins list     # 正式包（下划线复数）
    python -m genshen_skin list      # 本文件（下划线单数）

实现全在 `genshen_skins` 包里，这里只转发。
"""
import sys

from genshen_skins.cli import main

if __name__ == "__main__":
    sys.exit(main())
