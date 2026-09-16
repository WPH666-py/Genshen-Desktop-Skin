# -*- coding: utf-8 -*-
"""genshen_skins.catalog —— 读取 catalog.json，按关键词找到用户想要的那套皮肤。

catalog.json 同时存在于仓库根目录与包内（打包时随包发布），
两个副本由 `scripts/sync_catalog.py` 一次生成，内容一致。
"""
import json
import os

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE = None

_CANDIDATE_PATHS = (
    os.path.join(_PKG_DIR, "catalog.json"),                       # 随包发布
    os.path.join(os.path.dirname(_PKG_DIR), "catalog.json"),      # 源码仓库根目录
)


def catalog_path():
    for p in _CANDIDATE_PATHS:
        if os.path.exists(p):
            return p
    raise IOError("找不到 catalog.json（尝试过: %s）" % ", ".join(_CANDIDATE_PATHS))


def load_catalog(refresh=False):
    """加载皮肤目录。结果会缓存，refresh=True 时重新读盘。"""
    global _CACHE
    if _CACHE is not None and not refresh:
        return _CACHE
    with open(catalog_path(), encoding="utf-8") as f:
        _CACHE = json.load(f)
    return _CACHE


def skins():
    return load_catalog()["skins"]


def repo_url(repo):
    return "https://github.com/%s/%s" % (load_catalog()["owner"], repo)


def skin_repo_url(skin):
    return skin.get("url") or repo_url(skin["repo"])


def _norm(s):
    return (s or "").strip().lower()


def score(skin, key):
    """给一套皮肤与查询串的匹配度打分，越大越匹配；0 表示不匹配。

    优先级：id > 仓库名 > 角色中文名/英文名 > 皮肤名 > 别名 > 元素
    """
    k = _norm(key)
    if not k:
        return 0
    hits = [
        (1000, skin.get("id")),
        (900, skin.get("repo")),
        (880, skin.get("char")),
        (860, skin.get("charEn")),
        (800, skin.get("name")),
        (780, skin.get("nameEn")),
    ]
    best = 0
    for weight, value in hits:
        v = _norm(value)
        if not v:
            continue
        if v == k:
            best = max(best, weight + 10)
        elif k in v or v in k:
            best = max(best, weight)
    for alias in skin.get("aliases") or []:
        a = _norm(alias)
        if not a:
            continue
        if a == k:
            best = max(best, 700 + 10)
        elif k in a or a in k:
            best = max(best, 700)
    el = _norm(skin.get("element"))
    if el and el == k:
        best = max(best, 400)
    num = skin.get("no")
    if k.isdigit() and num is not None and int(k) == num:
        best = max(best, 950)
    return best


def find_skin(cat, key, default=None):
    """按 id / 仓库名 / 角色名 / 别名 / 序号找到一套皮肤。

    找不到返回 default（默认 None）；有多个同分候选时返回序号最小的那个。
    """
    key = (key or "").strip()
    if not key:
        return default
    ranked = sorted(
        ((score(s, key), -s.get("no", 9999), s) for s in cat["skins"]),
        key=lambda t: (-t[0], -t[1]),
    )
    if ranked and ranked[0][0] > 0:
        return ranked[0][2]
    return default


def search(cat, key):
    """返回所有匹配的皮肤（按匹配度排序），用于「用户说的名字有点模糊」时给候选。"""
    key = (key or "").strip()
    if not key:
        return []
    ranked = [t for t in ((score(s, key), s) for s in cat["skins"]) if t[0] > 0]
    ranked.sort(key=lambda t: -t[0])
    return [s for _sc, s in ranked]


def visible(skin):
    """返回该皮肤在本机可用的安装目标列表。"""
    caps = skin.get("caps") or {}
    out = []
    if caps.get("dsh"):
        out.append("dsh")
    if caps.get("vscode"):
        out.append("vscode")
    if caps.get("desktop"):
        out.append("desktop")
    if caps.get("deepking"):
        out.append("deepking")
    return out


def summary_row(skin):
    return "%s|%s|%s" % (skin["id"], skin["name"], skin.get("accent") or "")
