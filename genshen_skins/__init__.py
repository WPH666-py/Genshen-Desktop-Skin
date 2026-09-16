# -*- coding: utf-8 -*-
"""genshen_skins —— 原神桌面皮肤集合（Genshen Desktop Skin）的统一安装器。

29 套原神角色动态皮肤，一套素材多平台安装：

    DSH 动态插件 / VSCode·Trae·CodeX 扩展 / PyCharm 背景图 /
    DeepKing 规范包 / Windows 桌面置顶桌宠

用法::

    from genshen_skins import load_catalog, find_skin
    cat = load_catalog()
    skin = find_skin(cat, "skirk")

或直接用命令行::

    genshen-skin list
    genshen-skin install furina
"""
__version__ = "1.0.0"
__all__ = ["load_catalog", "find_skin", "skin_repo_url", "__version__"]

from .catalog import load_catalog, find_skin, skin_repo_url  # noqa: E402,F401
