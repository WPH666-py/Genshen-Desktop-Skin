# -*- coding: utf-8 -*-
"""sync_catalog.py —— 从 GitHub 重新生成 catalog.json。

catalog.json 是本集合的唯一事实来源(source of truth)：AI 助手、CLI、
README 都从它读取「有哪些皮肤、每套皮肤支持哪些环境、文件放在哪」。

当某个皮肤仓库新增了桌宠 / VSIX / 新壁纸时，重跑本脚本即可刷新整张能力矩阵：

    set GH_TOKEN=ghp_xxx                 # 可选；带上可避免 GitHub API 限流
    python scripts/sync_catalog.py        # 写回 catalog.json + genshen_skins/catalog.json
    python scripts/sync_catalog.py --check  # 只检查，不写入(CI 用)

SEED 只保存「稳定的身份信息」(中文名/英文名/别名/元素)，其余全部从各仓库实测：
  * skin.json                      —— 皮肤名、主题色、标语
  * git tree                       —— 真实存在的文件(能力矩阵的事实依据)
  * vscode-extension/package.json  —— 扩展 ID、显示名、命令 ID
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

OWNER = "WPH666-py"
HOME_REPO = "Genshen-Desktop-Skin"
PYPI_NAME = "genshen-desktop-skin"
BRANCH = "main"
API = "https://api.github.com"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# SEED：顺序 = README 中的展示顺序（沿用用户给定的顺序）
#   id       CLI 里用的短 id
#   repo     皮肤仓库名
#   char     角色中文名
#   charEn   角色英文名
#   element  神之眼元素（不确定的留空，不做臆测）
#   aliases  供 AI / 搜索匹配的别名
# ---------------------------------------------------------------------------
SEED = [
    ("citlali",   "Citlali",   "茜特拉莉",   "Citlali",       "冰", ["茜特菈莉", "citali", "qitealali", "紫粉星夜", "星夜"]),
    ("skirk",     "Skirk",     "丝柯克",     "Skirk",         "冰", ["skirk", "sikeke", "霜刃渊海", "渊海", "极恶技"]),
    ("keqing",    "Keqing",    "刻晴",       "Keqing",        "雷", ["keqing", "紫电雷鸣", "天街巡游", "玉衡星"]),
    ("furina",    "Furina",    "芙宁娜",     "Furina",        "水", ["furina", "funingna", "深蓝咏叹", "万众狂欢", "水神"]),
    ("hutao",     "Hutao",     "胡桃",       "Hutao",         "火", ["hutao", "焰蝶飞白", "蝶引来生", "往生堂"]),
    ("kokomi",    "Kokomi",    "珊瑚宫心海", "Kokomi",        "水", ["心海", "kokomi", "xinhai", "海月之誓", "珊瑚宫"]),
    ("ayaka",     "Ayaka",     "神里绫华",   "Kamisato Ayaka", "冰", ["绫华", "ayaka", "linghua", "霜雪冰刃", "神里"]),
    ("yoimiya",   "Yoimiya",   "宵宫",       "Yoimiya",       "火", ["yoimiya", "xiaogong", "琉金云间草", "烟花"]),
    ("lumine",    "Lumine",    "荧",         "Lumine",        "", ["lumine", "ying", "旅行者", "六元素", "女主"]),
    ("shenhe",    "Shenhe",    "申鹤",       "Shenhe",        "冰", ["shenhe", "shenhe", "神女遣灵真诀", "神女"]),
    ("eula",      "Eula",      "优菈",       "Eula",          "冰", ["eula", "youla", "凝浪之光剑", "浪花骑士"]),
    ("sucrose",   "Sucrose",   "砂糖",       "Sucrose",       "风", ["sucrose", "shatang", "风灵作成", "炼金"]),
    ("nicole",    "Nicole",    "尼可",       "Nicole",        "", ["nicole", "nike", "圣言默示", "天路历程"]),
    ("barbara",   "Barbara",   "芭芭拉",     "Barbara",       "水", ["barbara", "babala", "闪耀奇迹", "偶像"]),
    ("collei",    "Collei",    "柯莱",       "Collei",        "草", ["collei", "kelai", "猫猫秘宝", "柯莱"]),
    ("nilou",     "Nilou",     "妮露",       "Nilou",         "水", ["nilou", "nilu", "浮莲舞步", "远梦聆泉", "舞者"]),
    ("nahida",    "Nahida",    "纳西妲",     "Nahida",        "草", ["nahida", "naxida", "心景幻成", "草神", "小吉祥草王"]),
    ("shogun",    "Shogun",    "雷电将军",   "Raiden Shogun", "雷", ["雷电将军", "shogun", "raiden", "leidian", "梦想真说", "雷神", "影"]),
    ("ambor",     "Ambor",     "安柏",       "Amber",         "火", ["amber", "ambor", "anbo", "箭雨", "兔兔伯爵"]),
    ("yelan",     "Yelan",     "夜兰",       "Yelan",         "水", ["yelan", "yelan", "玄掷玲珑", "夜兰"]),
    ("zibai",     "Zibai",     "兹白",       "Zibai",         "", ["zibai", "zibai", "三垣威仪法", "兹白"]),
    ("ganyu",     "Ganyu",     "甘雨",       "Ganyu",         "冰", ["ganyu", "ganyu", "降众天华", "麒麟"]),
    ("columbina", "Columbina", "哥伦比娅",   "Columbina",     "", ["columbina", "gelunbiya", "她的乡愁", "少女", "愚人众"]),
    ("linnea",    "Linnea",    "莉奈娅",     "Linnea",        "", ["linnea", "linaiya", "绝境生存指南", "备忘"]),
    ("escoffier", "Escoffier", "爱可菲",     "Escoffier",     "冰", ["escoffier", "aikefei", "花刀技法", "爱可菲"]),
    ("navia",     "Navia",     "娜维娅",     "Navia",         "岩", ["navia", "naweiya", "如霰澄天的鸣礼", "刺玫会"]),
    ("mualani",   "Mualani",   "玛拉妮",     "Mualani",       "水", ["mualani", "malani", "爆瀑飞弹", "玛拉妮"]),
    ("sandrone",  "Sandrone",  "桑多涅",     "Sandrone",      "", ["sandrone", "sangduonie", "事象数式", "万理证毕", "木偶"]),
    ("clorinde",  "Clorinde",  "克洛琳德",   "Clorinde",      "雷", ["clorinde", "keluolinde", "秉烛剔星月", "决斗代理人"]),
    ("noelle",    "Noelle",    "诺艾尔",     "Noelle",        "岩", ["noelle", "nuoaier", "大扫除", "该打扫战场了", "西风骑士团", "女仆", "骑士"]),
    ("eneffa",    "Eneffa",    "伊涅芙",     "Eneffa",        "冰", ["eneffa", "yinefu", "霜蓝鎏金", "机械女仆", "剑势"], "Genshen-Eneffa-Skin"),
]


def token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_TK"):
        v = os.environ.get(key)
        if v:
            return v.strip()
    return None


def get(url, raw=False, timeout=30):
    """GET 一个 URL。raw=True 时返回文本，否则返回解析后的 JSON。"""
    req = urllib.request.Request(url, headers={"User-Agent": "genshen-skin-catalog"})
    tk = token()
    if tk and url.startswith(API):
        req.add_header("Authorization", "token %s" % tk)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if raw:
        return data.decode("utf-8", "replace")
    return json.loads(data.decode("utf-8"))


def _via_api(url):
    """raw.githubusercontent.com 不可达时, 改用 GitHub Contents API 取同一文件。

    raw 域名会整段返回 "SSL: UNEXPECTED_EOF_WHILE_READING"（不是 404），
    而 api.github.com 一直可用。两者内容一致, 只是传输方式不同。
    """
    import base64
    import re as _re
    m = _re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$", url)
    if not m:
        return None
    owner, repo, _branch, path = m.groups()
    data = get("%s/repos/%s/%s/contents/%s" % (API, owner, repo, path))
    if not isinstance(data, dict) or "content" not in data:
        return None
    try:
        text = base64.b64decode(data["content"]).decode("utf-8")
    except Exception:
        return None
    return json.loads(text)


def get_optional(url, tries=4):
    """GET，404 返回 None。

    raw.githubusercontent.com 会偶发超时/连接重置，甚至整段不可用。若直接吞掉
    这类错误，skin.json 与 package.json 就会读不到，导致 name/accent/tagline/ext
    静默退化成默认值（整张目录看起来"成功"、实则丢字段）。

    因此分两层兜底：
      1. 对瞬时网络错误退避重试；
      2. 仍失败则改走 GitHub Contents API 取同一文件。
    只有真正的 404 才返回 None。
    """
    last = None
    for attempt in range(tries):
        try:
            return get(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
        except Exception as e:
            last = e
        if attempt < tries - 1:
            time.sleep(1.0 * (attempt + 1))

    if url.startswith("https://raw.githubusercontent.com/"):
        for attempt in range(3):
            try:
                return _via_api(url)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                last = e
            except Exception as e:
                last = e
            time.sleep(1.5 * (attempt + 1))
        sys.stderr.write("[sync_catalog] API 兜底也失败: %s -> %s\n" % (url, last))
        return None

    sys.stderr.write("[sync_catalog] 读取失败(已重试 %d 次): %s -> %s\n"
                     % (tries, url, last))
    return None


def pick(paths, *candidates):
    for c in candidates:
        if c in paths:
            return c
    return None


def find_one(paths, predicate):
    for p in paths:
        if predicate(p):
            return p
    return None


def build_skin(entry, index):
    # 第 7 项可选：直接指定仓库名（默认按 Genshen-<Name>-Skin 推导）
    sid, repo_name, char, char_en, element, aliases = entry[:6]
    repo = entry[6] if len(entry) > 6 else "Genshen-%s-Skin" % repo_name
    url = "https://github.com/%s/%s" % (OWNER, repo)
    raw = "https://raw.githubusercontent.com/%s/%s/%s" % (OWNER, repo, BRANCH)

    skin = {
        "id": sid,
        "no": index,
        "repo": repo,
        "url": url,
        "raw": raw,
        "clone": "%s.git" % url,
        "char": char,
        "charEn": char_en,
        "element": element,
        "aliases": aliases,
        "name": "",
        "nameEn": "",
        "accent": "",
        "tagline": "",
        "caps": {"dsh": False, "desktop": False, "vscode": False, "deepking": False},
        "paths": {},
        "notes": [],
    }

    # ---- 1. git tree：能力矩阵的事实依据 ----
    tree = get_optional("%s/repos/%s/%s/git/trees/%s?recursive=1" % (API, OWNER, repo, BRANCH))
    if not tree:
        skin["notes"].append("GitHub 树读取失败：能力矩阵可能不完整")
        return skin
    paths = [e["path"] for e in tree.get("tree", []) if e.get("type") == "blob"]

    dsh_standalone = pick(paths, "dsh-plugin/client-standalone.js")
    dsh_client = pick(paths, "dsh-plugin/client.js", "client.js")
    dsh_host = pick(paths, "dsh-plugin/host.js", "host.js")
    vsix = find_one(paths, lambda p: p.startswith("vscode-extension/") and p.endswith(".vsix"))
    pkg = pick(paths, "vscode-extension/package.json")
    desktop_ps1 = find_one(paths, lambda p: p.startswith("desktop/") and p.endswith(".ps1"))
    desktop_bat = find_one(paths, lambda p: p.startswith("desktop/") and p.endswith(".bat"))
    deepking = pick(paths, "src/client/deepking-skin.module.css")
    skin_json = pick(paths, "skin.json")
    agents = pick(paths, "AGENTS.md")
    readme = pick(paths, "README.md", "仓库README.md")

    # DSH 客户端优先用零配置的 standalone；没有则退回仓库自己的 client.js
    # （丝柯克 / 刻晴的 client.js 本身已内嵌 base64 素材，见各自 AGENTS.md）
    client_for_dsh = dsh_standalone or dsh_client
    skin["caps"]["dsh"] = bool(client_for_dsh)
    skin["caps"]["desktop"] = bool(desktop_ps1 and desktop_bat)
    skin["caps"]["vscode"] = bool(vsix and pkg)
    skin["caps"]["deepking"] = bool(deepking)

    # 素材目录：桌宠脚本按 PSScriptRoot\素材 读取；刻晴等在仓库根目录直接放 素材/
    cand = sorted({p.rsplit("/", 1)[0] for p in paths if "/素材/" in p})
    if not cand and any(p.startswith("素材/") for p in paths):
        cand = ["素材"]
    # DSH 的素材目录优先跟随 client.js 所在目录（丝柯克 / 刻晴在根目录）
    dsh_dir = dsh_client.rsplit("/", 1)[0] if (dsh_client and "/" in dsh_client) else ""
    assets_dir = next((c for c in cand if c == (dsh_dir + "/素材").lstrip("/")), None) or (cand[0] if cand else None)

    # 壁纸与语音清单（供 wallpaper <id> <n> 与 AI 直接选用）
    home_assets = [p for p in paths if p.startswith((assets_dir + "/") if assets_dir else "\0")]
    wallpapers = sorted(p for p in home_assets
                        if p.lower().endswith(("-web.jpg", "-web.jpeg", "-web.png")))
    if not wallpapers:
        wallpapers = sorted(p for p in home_assets
                            if p.lower().endswith((".jpg", ".jpeg", ".png")) and "语音" not in p)
    voices = sorted(p for p in home_assets if "语音" in p and p.lower().endswith((".mp3", ".wav", ".ogg")))

    skin["paths"] = {
        "dsh_client": client_for_dsh,
        "dsh_client_standalone": dsh_standalone,
        "dsh_client_pair": dsh_client if dsh_standalone else None,
        "dsh_host": dsh_host,
        "dsh_assets": (dsh_client.rsplit("/", 1)[0] + "/素材") if (dsh_client and "/" in dsh_client) else "素材",
        "vsix": vsix,
        "ext_pkg": pkg,
        "desktop_ps1": desktop_ps1,
        "desktop_bat": desktop_bat,
        "desktop_assets": (desktop_ps1.rsplit("/", 1)[0] + "/素材") if (desktop_ps1 and "/" in desktop_ps1) else None,
        "deepking_css": deepking,
        "skin_json": skin_json,
        "agents_md": agents,
        "readme": readme,
        "assets": assets_dir,
    }
    skin["wallpapers"] = wallpapers
    skin["voices"] = voices

    # ---- 2. skin.json：主题名 / 主题色 ----
    if skin_json:
        data = get_optional("%s/%s" % (raw, skin_json))
        if isinstance(data, dict):
            skin["name"] = data.get("name") or ""
            skin["nameEn"] = data.get("nameEn") or ""
            skin["accent"] = data.get("accent") or ""
            skin["tagline"] = data.get("tagline") or ""
    if not skin["name"]:
        skin["name"] = char
    if not skin["accent"]:
        skin["accent"] = "#7a7f8c"

    # ---- 3. vscode-extension/package.json：扩展 ID / 显示名 / 命令 ----
    if pkg:
        data = get_optional("%s/%s" % (raw, pkg))
        if isinstance(data, dict):
            pub, nm = data.get("publisher") or "", data.get("name") or ""
            ext_id = ("%s.%s" % (pub, nm)).strip(".")
            cmds = [c.get("command") for c in ((data.get("contributes") or {}).get("commands") or [])]
            skin["ext"] = {
                "id": ext_id,
                "displayName": data.get("displayName") or "",
                "version": data.get("version") or "",
                "commands": [c for c in cmds if c],
                "show": next((c for c in cmds if c and c.endswith(".show")), None),
                "uninstall": next((c for c in cmds if c and c.endswith(".uninstall")), None),
            }
    if skin["caps"]["vscode"] and "ext" not in skin:
        skin["notes"].append("有 vsix 但读不到 package.json：扩展 ID 未知")

    # ---- 4. 能力缺口如实记录 ----
    if not dsh_standalone and dsh_client:
        skin["notes"].append("无 client-standalone.js，DSH 使用 %s（已内嵌素材，零配置可用）" % dsh_client)
    if not skin["caps"]["desktop"]:
        skin["notes"].append("该仓库暂未提供 Windows 桌宠脚本")
    if not skin["caps"]["vscode"]:
        skin["notes"].append("该仓库暂未打包 VSIX 扩展")
    if not skin["caps"]["deepking"]:
        skin["notes"].append("无 DeepKing 皮肤规范包(src/client/deepking-skin.module.css)")
    return skin


def build(verbose=True):
    skins = []
    for i, entry in enumerate(SEED, 1):
        if verbose:
            sys.stderr.write("[sync_catalog] %2d/%d  %s\n" % (i, len(SEED), entry[1]))
            sys.stderr.flush()
        skins.append(build_skin(entry, i))

    missing = [s["id"] for s in skins if not s["caps"]["dsh"] and not s["caps"]["desktop"] and not s["caps"]["vscode"]]
    catalog = {
        "schema": 1,
        "family": "原神桌面皮肤集合 · Genshen Desktop Skin",
        "owner": OWNER,
        "repo": HOME_REPO,
        "homepage": "https://github.com/%s/%s" % (OWNER, HOME_REPO),
        "pypi": PYPI_NAME,
        "cli": "genshen-skin",
        "count": len(skins),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "targets": {
            "dsh": "DeepSeek Harness 动态插件（cordis_define + cordis_run）",
            "vscode": "VSCode / Trae / CodeX / Cursor / Windsurf / VSCodium（VSIX 扩展）",
            "jetbrains": "PyCharm / IntelliJ / WebStorm（壁纸导出 + Background Image）",
            "desktop": "Windows 桌面置顶桌宠（覆盖 PyCharm / claude-code / kimi-code / CodeX 等一切窗口）",
            "deepking": "DeepKing 皮肤规范包（skin.json + CSS 变量 + 立绘）",
        },
        "usage": {
            "pip": "pip install %s" % PYPI_NAME,
            "list": "genshen-skin list",
            "install": "genshen-skin install <id>",
            "wallpaper": "genshen-skin wallpaper <id> <1|2|3|random>",
            "pet": "genshen-skin pet <id>",
            "ide": "genshen-skin ide <id>",
            "dsh": "genshen-skin dsh <id>",
        },
        "skins": skins,
    }
    if missing:
        catalog["warnings"] = ["以下皮肤仓库没有任何可安装目标：%s" % ", ".join(missing)]
    return catalog


def prepare_console():
    """Windows GBK 控制台避免 Unicode 打印崩溃。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main(argv=None):
    prepare_console()
    ap = argparse.ArgumentParser(description="从 GitHub 重新生成 catalog.json")
    ap.add_argument("--check", action="store_true", help="只检查，不写文件")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    cat = build(verbose=not args.quiet)
    text = json.dumps(cat, ensure_ascii=False, indent=2) + "\n"

    targets = [os.path.join(ROOT, "catalog.json"),
               os.path.join(ROOT, "genshen_skins", "catalog.json")]
    if args.check:
        for t in targets:
            if not os.path.exists(t):
                print("缺失: %s" % t)
                return 1
            old = open(t, encoding="utf-8").read()
            same = json.loads(old)["skins"] == cat["skins"]
            print("%s: %s" % (t, "一致" if same else "有差异(需要重跑 sync_catalog.py)"))
        return 0

    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("[sync_catalog] 已写入 %s" % t)
    print("[sync_catalog] %d 套皮肤" % cat["count"])
    for s in cat["skins"]:
        flags = "".join(k[0].upper() if v else "-" for k, v in s["caps"].items())
        print("  %-10s %-22s %s  %s" % (s["id"], s["name"], flags, s["accent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
