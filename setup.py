"""setup.py —— 兼容老版本 pip（真正的元数据在 pyproject.toml）。

早期 pip 不支持 pyproject.toml 的 [project] 表，这里做一次等价声明，
让 `pip install .` 在 Python 3.8 + 老 pip 上也能工作。
"""
from setuptools import setup

setup(
    name="genshen-desktop-skin",
    version="1.0.9",
    description="原神桌面皮肤集合（33 套）：壁纸 / IDE 扩展 / DSH 插件 / Windows 桌宠 一键安装",
    author="WPH666-py",
    url="https://github.com/WPH666-py/Genshen-Desktop-Skin",
    license="MIT",
    packages=["genshen_skins"],
    # 顶层兼容入口：让 `python -m genshen-skin` / `python -m genshen_skin` 也能用
    py_modules=["genshen-skin", "genshen_skin"],
    package_data={"genshen_skins": ["catalog.json", "assets/*.ps1", "assets/*.bat"]},
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "genshen-skin = genshen_skins.cli:main",
            "gss = genshen_skins.cli:main",
        ],
    },
)
