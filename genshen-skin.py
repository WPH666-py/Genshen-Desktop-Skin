# -*- coding: utf-8 -*-
"""`python -m genshen-skin` 的入口。

为什么这个文件叫 `genshen-skin.py`（带连字符）：
    用户很自然会试着敲 `python -m genshen-skin`（因为 pip 的发行名和命令名都是
    连字符写法），而 `python -m` 是按**字符串**去 sys.path 里找模块的，不要求名字是
    合法标识符 —— 所以带连字符的模块文件是能被 `-m` 找到并执行的。

    对比一下（实测结论）：
        python -m genshen-skin      ✔ 可以（本文件）
        importlib.import_module("genshen-skin")   ✔ 可以（字符串查找）
        import genshen-skin         ✘ SyntaxError（import 语句要求合法标识符）
        from genshen-skin import x  ✘ SyntaxError

    因此本文件作为**顶层兼容入口**随包发布，让下面四种写法完全等价：

        genshen-skin list                 # 控制台命令（别名 gss）
        python -m genshen-skin list       # 本文件
        python -m genshen_skins list      # 正式包（下划线）
        python -m genshen_skin list       # 下划线单数别名

    真正的实现都在 `genshen_skins` 包里，这里只做转发，不放任何业务逻辑。
"""
import sys

from genshen_skins.cli import main

if __name__ == "__main__":
    sys.exit(main())
