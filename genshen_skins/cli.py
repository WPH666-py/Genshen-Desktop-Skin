# -*- coding: utf-8 -*-
"""genshen_skins.cli —— `genshen-skin` 命令行。

    genshen-skin list                      列出 31 套皮肤
    genshen-skin show <角色>               某套详情与安装方式
    genshen-skin env                       体检本机环境（IDE / DSH / 代理 / 屏幕）
    genshen-skin install <角色>            一键安装（壁纸 + 扩展 + 桌宠）
    genshen-skin wallpaper <角色> [模式]   切换桌面壁纸（1/2/3/random）
    genshen-skin export <角色>             导出全部壁纸（给 PyCharm 等用）
    genshen-skin pet <角色>                启动桌面桌宠（--stop/--autostart/--uninstall）
    genshen-skin ide <角色>                安装 VSIX 到 VSCode/Trae/CodeX…
    genshen-skin dsh <角色>                准备 DSH 动态插件载荷
    genshen-skin deepking <角色>           导出 DeepKing 皮肤规范包
    genshen-skin sync [角色|--all]         克隆皮肤仓库到本地
    genshen-skin vendor --out <目录>       把 31 个仓库全部落地（离线收藏）
    genshen-skin doctor                    体检：代理 / 网络 / 镜像 / git / Pillow
    genshen-skin uninstall <角色>          卸载（扩展 / 桌宠 / 本地副本）
"""
import argparse
import json
import os
import sys

from . import __version__
from . import catalog as cat_mod
from . import desktop, dsh, mirror, proxy, repo, targets, wallpaper

CAP_LABEL = {
    "dsh": "DSH",
    "desktop": "桌宠",
    "vscode": "IDE扩展",
    "deepking": "DeepKing",
}


def prepare_console():
    """Windows GBK 控制台避免 Unicode 打印崩溃。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def mirror_name(args):
    m = getattr(args, "mirror", None) or os.environ.get("GENSHEN_MIRROR") or "tuna"
    return m if m in mirror.PIP_MIRRORS else "tuna"


def resolve(key, cat=None, strict=True):
    """把用户输入解析成一套皮肤；找不到时给候选提示。"""
    cat = cat or cat_mod.load_catalog()
    skin = cat_mod.find_skin(cat, key)
    if skin:
        return skin
    cands = cat_mod.search(cat, key)
    if cands:
        print("没找到 %r，你是不是想要：" % key, file=sys.stderr)
        for s in cands[:6]:
            print("  %-10s %s" % (s["id"], s["name"]), file=sys.stderr)
    else:
        print("没找到 %r。用 `genshen-skin list` 看全部 31 套。" % key, file=sys.stderr)
    if strict:
        raise SystemExit(2)
    return None


def caps_text(skin):
    caps = skin.get("caps") or {}
    return " ".join(CAP_LABEL[k] for k in CAP_LABEL if caps.get(k)) or "（无）"


# ---------------------------------------------------------------------------
# list / show / catalog
# ---------------------------------------------------------------------------
def cmd_list(args):
    cat = cat_mod.load_catalog()
    print("原神桌面皮肤集合 · 共 %d 套" % cat["count"])
    print("仓库: %s" % cat["homepage"])
    print()
    print("%-3s %-10s %-20s %-8s %-6s %s" % ("#", "ID", "皮肤", "元素", "序号", "可用环境"))
    print("-" * 78)
    for s in cat["skins"]:
        cap = "".join("●" if (s["caps"] or {}).get(k) else "○" for k in ("dsh", "vscode", "desktop", "deepking"))
        print("%-3d %-10s %-20s %-8s %-6s %s" % (
            s["no"], s["id"], s["name"], s.get("element") or "-", cap, caps_text(s)))
    print()
    print("环境图例: ●DSH ●IDE扩展 ●桌宠 ●DeepKing   (○ = 该仓库暂未提供)")
    print("装某套:  genshen-skin install <ID>        例: genshen-skin install skirk")
    return 0


def cmd_show(args):
    skin = resolve(args.key)
    paths = skin.get("paths") or {}
    print("%s" % skin["name"])
    print("  ID / 仓库   : %s / %s" % (skin["id"], skin["repo"]))
    print("  角色 / 元素 : %s %s" % (skin["char"], skin.get("element") or "-"))
    print("  主题色      : %s" % skin.get("accent"))
    if skin.get("tagline"):
        print("  标语        : %s" % skin["tagline"])
    print("  仓库地址    : %s" % skin["url"])
    print("  可用环境    : %s" % caps_text(skin))
    print()
    print("  壁纸 %d 张:" % len(skin.get("wallpapers") or []))
    for i, w in enumerate(skin.get("wallpapers") or [], 1):
        print("    %d. %s" % (i, os.path.basename(w)))
    if skin.get("voices"):
        print("  语音 %d 个: %s" % (len(skin["voices"]),
                                   "、".join(os.path.basename(v) for v in skin["voices"][:4])))
    if skin.get("ext"):
        print("  扩展 ID     : %s  (%s)" % (skin["ext"].get("id"), skin["ext"].get("displayName")))
        if skin["ext"].get("show"):
            print("  显示命令    : %s" % skin["ext"]["show"])
    if skin.get("notes"):
        print()
        print("  说明:")
        for n in skin["notes"]:
            print("    · %s" % n)
    print()
    print("  安装:")
    print("    genshen-skin install %s          # 一键（按本机环境自动选择）" % skin["id"])
    print("    genshen-skin wallpaper %s 1      # 只换壁纸" % skin["id"])
    if (skin["caps"] or {}).get("desktop"):
        print("    genshen-skin pet %s              # 桌面桌宠" % skin["id"])
    if (skin["caps"] or {}).get("vscode"):
        print("    genshen-skin ide %s              # 装 VSIX 扩展" % skin["id"])
    if (skin["caps"] or {}).get("dsh"):
        print("    genshen-skin dsh %s              # DSH 动态插件载荷" % skin["id"])
    return 0


def cmd_catalog(args):
    cat = cat_mod.load_catalog()
    if args.json:
        print(json.dumps(cat, ensure_ascii=False, indent=2))
        return 0
    if args.md:
        print("# %s" % cat["family"])
        print()
        print("| # | ID | 皮肤 | 角色 | 元素 | 主题色 | 壁纸 | DSH | IDE扩展 | 桌宠 | DeepKing | 仓库 |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for s in cat["skins"]:
            c = s["caps"]
            print("| %d | `%s` | %s | %s | %s | `%s` | %d | %s | %s | %s | %s | [%s](%s) |" % (
                s["no"], s["id"], s["name"], s["char"], s.get("element") or "-",
                s.get("accent"), len(s.get("wallpapers") or []),
                "✅" if c.get("dsh") else "—", "✅" if c.get("vscode") else "—",
                "✅" if c.get("desktop") else "—", "✅" if c.get("deepking") else "—",
                s["repo"], s["url"]))
        return 0
    print("catalog: %s" % cat_mod.catalog_path())
    print("共 %d 套，schema=%s，生成于 %s" % (cat["count"], cat["schema"], cat.get("generated_at")))
    return 0


# ---------------------------------------------------------------------------
# env / doctor
# ---------------------------------------------------------------------------
def cmd_env(args):
    info = targets.describe_env()
    print("原神皮肤集合 · 本机环境")
    print()
    print("系统        : %s" % info["platform"])
    print("Python      : %s" % info["python"])
    print("git         : %s" % (info["git"] or "未安装（桌宠/壁纸仍可用，克隆会退回源码包下载）"))
    print("屏幕        : %dx%d" % tuple(info["screen"]))
    print("Pillow      : %s" % ("已安装" if info["pillow"] else "未安装（合成壁纸时会自动装）"))
    print("代理        : %s" % (info["proxy"]["url"] or "未探测到"))
    if info["proxy"]["url"]:
        print("              来源: %s" % info["proxy"]["source"])
    print("DSH         : %s" % info["dsh"]["note"])
    print("AI 助手环境 : %s" % ("、".join(info["agent_cli"]) or "未识别"))
    print()
    eds = info["editors"]
    if eds:
        print("检测到的编辑器（可装 VSIX）:")
        for ed in eds:
            print("  · %-10s %s" % (ed["name"], ed["cli"] or ("扩展目录 %s" % ed["extdir"])))
    else:
        print("未检测到 VSCode / Trae / CodeX 等编辑器（可只用桌宠 + 壁纸）")
    jb = info["jetbrains"]
    if jb:
        print()
        print("检测到的 JetBrains 系（PyCharm 等，用壁纸导出）:")
        for j in jb[:8]:
            print("  · %s" % j["name"])
    print()
    print("本地目录: %s" % repo.home_dir())
    return 0


def cmd_doctor(args):
    import platform
    import ssl
    import urllib.request

    print("# genshen-skin 体检")
    print()
    print("Python      : %s (%s)" % (platform.python_version(), sys.executable))
    print("系统        : %s %s" % (platform.system(), platform.release()))
    print("包版本      : genshen-desktop-skin %s" % __version__)
    print("目录        : %s" % repo.home_dir())

    # git
    try:
        import subprocess
        gv = subprocess.run(["git", "--version"], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=10, text=True).stdout.strip()
        print("git         : %s" % (gv or "可用"))
    except Exception as e:
        print("git         : 不可用 (%s) —— 会退回源码包下载" % e)

    # Pillow
    print("Pillow      : %s" % ("已安装" if wallpaper.have_pillow() else "未安装（会自动装）"))

    # 代理
    print()
    print("— 代理 —")
    url, source = proxy.detect(force=True)
    print("探测结果    : %s" % (url or "未探测到"))
    print("来源        : %s" % (source or "无"))
    print("说明        : pip / urllib 只认 HTTP_PROXY / HTTPS_PROXY 环境变量，")
    print("              不读 Windows 系统代理；本工具会把探测结果显式传给 git/pip。")
    print("关闭探测    : GENSHEN_NO_PROXY=1    手动指定: GENSHEN_PROXY=http://host:port")

    # 网络
    print()
    print("— 网络（HTTPS 实测）—")

    def https_ok(u, timeout=10):
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "genshen-doctor"})
        try:
            with proxy.opener().open(req, timeout=timeout) as r:
                return True, "HTTP %d" % r.status
        except Exception as e:
            reason = getattr(e, "reason", None)
            if isinstance(reason, ssl.SSLError):
                return False, "TLS 握手失败(%s)" % reason.__class__.__name__
            return False, str(reason or e)[:46]

    # 国内镜像逐个实测 —— 直接遍历 mirror.MIRROR_ORDER，镜像表一变这里自动跟上
    # （此前只硬编码了清华与中科大，mirror.py 里明明有阿里云却测不到）
    checks = [
        ("GitHub 直连", "https://github.com"),
        ("raw.githubusercontent", "https://raw.githubusercontent.com"),
        ("jsDelivr CDN", "https://cdn.jsdelivr.net"),
        ("PyPI 官方源", "https://pypi.org/simple/"),
    ] + [
        ("%s 镜像" % mirror.PIP_MIRRORS[k]["name"], mirror.PIP_MIRRORS[k]["index"] + "/")
        for k in mirror.MIRROR_ORDER
    ]
    res = {}
    for label, u in checks:
        ok, note = https_ok(u)
        res[label] = ok
        print("  %-26s %-44s %s" % (label, note, "✅" if ok else "❌"))

    # 结论
    print()
    working = [k for k in mirror.MIRROR_ORDER
               if res.get("%s 镜像" % mirror.PIP_MIRRORS[k]["name"])]
    px = mirror.py_prefix()
    if res.get("PyPI 官方源"):
        print("结论: pypi.org 正常，%s pip install genshen-desktop-skin 可直接用。" % px)
        if working:
            print("      国内网络想更快，或用任一可用镜像：")
            for k in working:
                print("      %s pip install -i %s genshen-desktop-skin   # %s"
                      % (px, mirror.PIP_MIRRORS[k]["index"], mirror.PIP_MIRRORS[k]["name"]))
    elif working:
        print("结论: pypi.org 连不上，但以下镜像可用（任选一条）：")
        for k in working:
            print("  %s pip install -i %s genshen-desktop-skin   # %s"
                  % (px, mirror.PIP_MIRRORS[k]["index"], mirror.PIP_MIRRORS[k]["name"]))
    else:
        print("结论: PyPI 与全部国内镜像都连不上，请检查网络或代理设置。")

    if res.get("GitHub 直连"):
        print("结论: GitHub 可直连，克隆皮肤仓库没问题。")
    else:
        print("结论: GitHub 直连不通 —— 本工具会自动改用加速通道（jsDelivr / ghfast / gitmirror …）。")
    return 0


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------
def do_wallpaper(skin, args, quiet=False):
    try:
        return wallpaper.apply_skin_wallpaper(
            skin, mode=args.mode, size=wallpaper.parse_size(getattr(args, "size", None)),
            fit=getattr(args, "fit", None) or wallpaper.FIT_BLUR,
            mirror_name=mirror_name(args), quiet=quiet)
    except Exception as e:
        print("[genshen] 壁纸设置失败: %s" % e, file=sys.stderr)
        return None


def do_ide(skin, args, quiet=False):
    if not (skin["caps"] or {}).get("vscode"):
        if not quiet:
            print("[genshen] %s 暂未提供 VSIX 扩展，跳过 IDE 安装" % skin["char"])
        return []
    eds = targets.detect_editors()
    if getattr(args, "editor", None):
        one = targets.find_editor(args.editor)
        if not one:
            print("[genshen] 没找到编辑器 %r" % args.editor, file=sys.stderr)
            return []
        eds = [one]
    if not eds:
        if not quiet:
            print("[genshen] 没检测到 VSCode / Trae / CodeX 等编辑器，跳过扩展安装")
        return []

    vsix_rel = (skin.get("paths") or {}).get("vsix")
    local = repo.ensure_repo(skin["repo"], url=skin.get("clone"), quiet=quiet)
    vsix = os.path.join(local, vsix_rel)
    if not os.path.exists(vsix):
        repo.download_to(skin["repo"], vsix_rel, vsix, quiet=quiet)

    done = []
    for ed in eds:
        ok, note = targets.install_vsix(ed, vsix, quiet=quiet)
        print("[genshen] %s: %s" % (ed["name"], note))
        if ok:
            done.append(ed["name"])
            if skin.get("ext", {}).get("show"):
                print("          命令面板(Ctrl+Shift+P) → 「%s」" % skin["ext"].get("displayName", ""))
    return done


def do_pet(skin, args, quiet=False):
    if not (skin["caps"] or {}).get("desktop"):
        if not quiet:
            print("[genshen] %s 仓库没有自带桌宠，改用内置通用桌宠" % skin["char"])
        generic = True
    else:
        generic = bool(getattr(args, "generic", False))
    return desktop.launch(skin, generic=generic, quiet=quiet)


def cmd_install(args):
    skin = resolve(args.key)
    print("=== 安装 %s ===" % skin["name"])
    print("仓库 %s" % skin["url"])
    print()

    did = []
    # 1) 壁纸
    if not args.no_wallpaper:
        if do_wallpaper(skin, args):
            did.append("桌面壁纸")
    # 2) IDE 扩展
    if not args.no_ide:
        if do_ide(skin, args):
            did.append("IDE 扩展")
    # 3) 桌宠
    if not args.no_pet:
        caps = skin["caps"] or {}
        if caps.get("desktop") or args.force_pet:
            try:
                do_pet(skin, args)
                did.append("桌面桌宠")
            except Exception as e:
                print("[genshen] 桌宠启动失败: %s" % e, file=sys.stderr)

    print()
    if did:
        print("完成：%s" % "、".join(did))
    else:
        print("没有安装任何目标（可能都被 --no-* 跳过了）")

    if (skin["caps"] or {}).get("dsh") and not args.no_dsh:
        print()
        print("想在 DeepSeek Harness 里用这套皮？执行：")
        print("  genshen-skin dsh %s        # 生成载荷，并把步骤交给 AI" % skin["id"])
    print()
    print("后续：")
    print("  换壁纸   genshen-skin wallpaper %s 2" % skin["id"])
    if (skin["caps"] or {}).get("desktop"):
        print("  停桌宠   genshen-skin pet %s --stop" % skin["id"])
    print("  卸载     genshen-skin uninstall %s" % skin["id"])
    return 0


# ---------------------------------------------------------------------------
# wallpaper / export
# ---------------------------------------------------------------------------
def cmd_wallpaper(args):
    skin = resolve(args.key)
    if args.list:
        print("%s 的壁纸（%d 张）:" % (skin["name"], len(skin.get("wallpapers") or [])))
        for i, w in enumerate(skin.get("wallpapers") or [], 1):
            print("  %d. %s" % (i, os.path.basename(w)))
        print()
        print("用法: genshen-skin wallpaper %s <1..%d|random>" % (skin["id"], len(skin.get("wallpapers") or [1])))
        return 0
    out = do_wallpaper(skin, args)
    return 0 if out else 1


def cmd_export(args):
    skin = resolve(args.key)
    made = wallpaper.export_all(skin, out_dir=args.out, size=wallpaper.parse_size(args.size),
                               fit=args.fit or wallpaper.FIT_BLUR,
                               mirror_name=mirror_name(args))
    print()
    print("已导出 %d 张到 %s" % (len(made), os.path.dirname(made[0]) if made else args.out))
    print("PyCharm / IntelliJ 用法：Settings → Appearance & Behavior → Background Image → 选其中一张")
    return 0 if made else 1


# ---------------------------------------------------------------------------
# pet
# ---------------------------------------------------------------------------
def cmd_pet(args):
    skin = resolve(args.key)
    if args.uninstall:
        return 0 if desktop.uninstall(skin) else 1
    if args.stop:
        desktop.stop(skin)
        return 0
    if args.autostart is not None:
        ok, note = desktop.set_autostart(skin, enable=args.autostart,
                                         generic=args.generic or not (skin["caps"] or {}).get("desktop"))
        print("[genshen] %s" % note)
        return 0 if ok else 1
    if desktop.running(skin):
        print("[genshen] %s 桌宠已经在运行" % skin["char"])
        return 0
    do_pet(skin, args)
    return 0


# ---------------------------------------------------------------------------
# ide
# ---------------------------------------------------------------------------
def cmd_ide(args):
    if args.list:
        eds = targets.detect_editors()
        if not eds:
            print("没检测到 VSCode / Trae / CodeX / Cursor / Windsurf / VSCodium")
            return 1
        print("检测到的编辑器:")
        for ed in eds:
            print("  · %-10s %s" % (ed["name"], ed["cli"] or ed["extdir"]))
        return 0

    skin = resolve(args.key)
    if args.uninstall:
        ext_id = (skin.get("ext") or {}).get("id")
        if not ext_id:
            print("[genshen] %s 没有登记扩展 ID" % skin["id"], file=sys.stderr)
            return 1
        target_eds = ([targets.find_editor(args.editor)] if args.editor
                      else targets.installed_vsix_editors(ext_id))
        if not target_eds or not any(target_eds):
            print("[genshen] 没找到已安装 %s 的编辑器" % ext_id)
            return 1
        for ed in target_eds:
            if ed:
                ok, note = targets.uninstall_vsix(ed, ext_id)
                print("[genshen] %s: %s" % (ed["name"], note))
        return 0
    return 0 if do_ide(skin, args) else 1


# ---------------------------------------------------------------------------
# dsh / deepking
# ---------------------------------------------------------------------------
def cmd_dsh(args):
    skin = resolve(args.key)
    if not (skin["caps"] or {}).get("dsh"):
        print("[genshen] %s 没有可用的 DSH 客户端文件" % skin["id"], file=sys.stderr)
        return 1
    dsh.emit(skin, quiet=args.quiet, with_host=args.with_host, as_json=args.json)
    return 0


def cmd_deepking(args):
    skin = resolve(args.key)
    css_rel = (skin.get("paths") or {}).get("deepking_css")
    if not css_rel:
        print("[genshen] %s 没有 DeepKing 皮肤规范包" % skin["id"], file=sys.stderr)
        return 1
    out = os.path.abspath(args.out or os.path.join(repo.home_dir(), "_deepking", skin["id"]))
    os.makedirs(out, exist_ok=True)
    made = []
    for rel in (css_rel, (skin.get("paths") or {}).get("skin_json")):
        if not rel:
            continue
        dest = os.path.join(out, os.path.basename(rel))
        repo.download_to(skin["repo"], rel, dest, quiet=True)
        made.append(dest)
    # 立绘
    for rel in (skin.get("wallpapers") or [])[:1]:
        dest = os.path.join(out, os.path.basename(rel))
        repo.download_to(skin["repo"], rel, dest, quiet=True)
        made.append(dest)
    manifest = {
        "id": skin["id"], "name": skin["name"], "nameEn": skin.get("nameEn"),
        "char": skin["char"], "accent": skin.get("accent"), "tagline": skin.get("tagline"),
        "repo": skin["url"], "files": [os.path.basename(m) for m in made],
    }
    with open(os.path.join(out, "genshen-skin.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("[genshen] DeepKing 皮肤包已导出到 %s" % out)
    for m in made:
        print("  · %s" % m)
    return 0


# ---------------------------------------------------------------------------
# sync / vendor
# ---------------------------------------------------------------------------
def cmd_sync(args):
    cat = cat_mod.load_catalog()
    if args.all:
        items = cat["skins"]
    else:
        items = [resolve(args.key, cat)]
    for s in items:
        try:
            repo.ensure_repo(s["repo"], url=s.get("clone"), quiet=True)
            print("[genshen] ✓ %-12s %s" % (s["id"], repo.skin_dir(s["repo"])))
        except Exception as e:
            print("[genshen] ✗ %-12s %s" % (s["id"], e), file=sys.stderr)
    print()
    print("本地目录: %s" % repo.home_dir())
    return 0


def cmd_vendor(args):
    """把全部皮肤仓库落地到指定目录（离线收藏 / 自建镜像用）。"""
    cat = cat_mod.load_catalog()
    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out, exist_ok=True)
    old_home = os.environ.get("GENSHEN_HOME")
    os.environ["GENSHEN_HOME"] = out
    ok = fail = 0
    try:
        for s in cat["skins"]:
            dst = os.path.join(out, s["repo"])
            if os.path.isdir(dst) and not args.force:
                print("[genshen] 跳过（已存在）%s" % s["repo"])
                ok += 1
                continue
            try:
                repo.ensure_repo(s["repo"], url=s.get("clone"), quiet=True)
                print("[genshen] ✓ %s" % s["repo"])
                ok += 1
            except Exception as e:
                print("[genshen] ✗ %s: %s" % (s["repo"], e), file=sys.stderr)
                fail += 1
    finally:
        if old_home is None:
            os.environ.pop("GENSHEN_HOME", None)
        else:
            os.environ["GENSHEN_HOME"] = old_home
    print()
    print("完成：成功 %d，失败 %d，目录 %s" % (ok, fail, out))
    return 1 if fail else 0


# ---------------------------------------------------------------------------
# mirror / uninstall
# ---------------------------------------------------------------------------
def show_mirrors():
    print("PyPI 镜像（用于 pip install）")
    print()
    print("%-10s %-22s %s" % ("别名", "名称", "index-url"))
    print("-" * 82)
    for k, m in mirror.PIP_MIRRORS.items():
        print("%-10s %-22s %s" % (k, m["name"], m["index"]))
    print()
    print("国内装包（推荐，任选一条）：")
    px = mirror.py_prefix()
    for k in mirror.MIRROR_ORDER:
        print("  %s pip install -i %s genshen-desktop-skin   # %s"
              % (px, mirror.PIP_MIRRORS[k]["index"], mirror.PIP_MIRRORS[k]["name"]))
    print()
    print("说明：上述国内源都是 PyPI 的**只读镜像**，会自动从 pypi.org 同步；")
    print("      作者只能发布到 PyPI，镜像随后自动收录（清华通常几分钟内）。")
    print("      发布后可用以下地址确认镜像是否已同步：")
    for k in mirror.MIRROR_ORDER:
        print("        %-58s %s" % (mirror.PIP_MIRRORS[k]["web"], mirror.PIP_MIRRORS[k]["name"]))
    print()
    print("GitHub 加速通道（用于克隆皮肤仓库 / 下载 raw 文件）")
    print()
    for p in mirror.GITHUB_PROXIES:
        kinds = []
        if p.get("clone") is not None:
            kinds.append("clone")
        if p.get("raw") is not None:
            kinds.append("raw")
        print("  %-12s %-16s %s" % (p["id"], p["name"], " / ".join(kinds) or "—"))
    print()
    print("本工具会自动按顺序尝试这些通道，第一个成功的会被记住。")


def cmd_mirror(args):
    if args.set:
        name = args.set
        if name not in mirror.PIP_MIRRORS:
            print("未知镜像 %r，可用: %s" % (name, ", ".join(mirror.PIP_MIRRORS)), file=sys.stderr)
            return 2
        m = mirror.PIP_MIRRORS[name]
        print("已把默认镜像设为 %s" % m["name"])
        print()
        print("本次会话生效（PowerShell）:")
        print('  $env:GENSHEN_MIRROR = "%s"' % name)
        print("永久生效（PowerShell）:")
        print('  [Environment]::SetEnvironmentVariable("GENSHEN_MIRROR", "%s", "User")' % name)
        print()
        print("也可以直接给 pip 配镜像:")
        print("  pip config set global.index-url %s" % m["index"])
        return 0
    show_mirrors()
    env = mirror.env_hint()
    if env:
        print()
        print("当前环境变量: %s" % ", ".join("%s=%s" % kv for kv in env.items()))
    return 0


def cmd_uninstall(args):
    skin = resolve(args.key)
    print("=== 卸载 %s ===" % skin["name"])
    # 1) VSIX
    ext_id = (skin.get("ext") or {}).get("id")
    if ext_id:
        for ed in targets.installed_vsix_editors(ext_id):
            ok, note = targets.uninstall_vsix(ed, ext_id)
            print("[genshen] %s: %s" % (ed["name"], note))
    # 2) 桌宠
    desktop.uninstall(skin, quiet=True)
    print("[genshen] 桌宠与开机自启已清理")
    # 3) 本地副本
    if not args.keep_files:
        for d in (repo.skin_dir(skin["repo"]), desktop.pet_dir(skin), dsh.work_dir(skin)):
            if not os.path.isdir(d):
                continue
            if repo.rmtree(d):
                print("[genshen] 已删除 %s" % d)
            else:
                left = sum(1 for _ in os.scandir(d)) if os.path.isdir(d) else 0
                print("[genshen] 未能完全删除 %s（可能被占用，剩余 %d 项）" % (d, left),
                      file=sys.stderr)
                print("[genshen]   手动删除: rmdir /s /q \"%s\"" % d, file=sys.stderr)
    print()
    print("完成。DSH 动态插件请在 DSH 里 cordis_undefine <pluginId> 移除，")
    print("或直接用皮肤上的右键菜单「一键卸载」。")
    return 0


def cmd_paths(args):
    cat = cat_mod.load_catalog()
    print("本地根目录 : %s" % repo.home_dir())
    print("皮肤仓库   : %s" % os.path.join(repo.home_dir(), "<仓库名>"))
    print("壁纸输出   : %s" % wallpaper.wall_dir())
    print("桌宠目录   : %s" % desktop.pets_home())
    print("DSH 载荷   : %s" % dsh.dsh_home())
    print("catalog    : %s" % cat_mod.catalog_path())
    print()
    cloned = [s for s in cat["skins"] if repo.is_cloned(repo.skin_dir(s["repo"]))]
    print("已克隆 %d/%d 套: %s" % (len(cloned), cat["count"],
                                  "、".join(s["id"] for s in cloned) or "（无）"))
    return 0


# ---------------------------------------------------------------------------
# 全部命令总览
# ---------------------------------------------------------------------------
COMMANDS_HELP = """原神桌面皮肤集合 · 全部命令总览

用法： genshen-skin <命令> [参数]        直接敲 `genshen-skin` 就是这一页

── 看目录 ─────────────────────────────────────────────────────────
  list                     列出全部 31 套皮肤与各自可用环境
  show <角色>              某套皮肤详情（壁纸清单 / 扩展 ID / 安装方式）
  catalog                  打印机器可读目录      --md 表格  --json 原始
  paths                    显示各类本地目录

── 装 / 卸 ─────────────────────────────────────────────────────────
  install <角色>           一键安装：桌面壁纸 + IDE 扩展 + 桌面桌宠
       --mode 1|2|3|random      指定壁纸（默认 random）
       --fit blur|cover|contain 壁纸适配（默认 blur，无黑边）
       --editor vscode|trae|codex   只装到指定编辑器
       --no-wallpaper / --no-ide / --no-pet   跳过其中某一步
  uninstall <角色>         卸载：IDE 扩展 + 桌宠 + 开机自启 + 本地副本
       --keep-files             保留已下载的素材（下次换壁纸不用重下）

── 单平台 ──────────────────────────────────────────────────────────
  wallpaper <角色> [模式]  切换桌面壁纸（模式：1 / 2 / 3 / random / --list）
  export <角色> [--out 目录]     导出整屏壁纸给 PyCharm / JetBrains 当背景图
  pet <角色>               桌面桌宠；--stop 停 / --autostart 开机自启 /
                           --no-autostart 关自启 / --uninstall 卸桌宠
  ide <角色>               VSIX 扩展；--list 看编辑器 / --editor 指定 / --uninstall 卸
  dsh <角色>               DeepSeek Harness 动态插件载荷（--with-host 全画质）
  deepking <角色>          DeepKing 皮肤规范包（--out 指定目录）

── 镜像 / 同步 ─────────────────────────────────────────────────────
  sync --all               克隆 31 个仓库到 ~/.genshen-skins
  vendor --out <目录>      把 31 个仓库全部落地到指定目录（离线收藏）
  mirror                   查看 pip 镜像与 GitHub 加速通道
       --set tuna|ustc|aliyun|tencent|official   设为默认镜像

── 诊断 ────────────────────────────────────────────────────────────
  env                      检测本机环境（IDE / DSH / 代理 / 屏幕分辨率）
  doctor                   体检：代理 / 网络 / 镜像 / git / Pillow
  commands                 显示本页

角色可以用中文名、英文名、拼音或别名，例如：
  芙宁娜 = 水神 = furina      纳西妲 = 草神 = nahida
  雷电将军 = 雷神 = shogun    神里绫华 = 绫华 = ayaka

常用示例
  genshen-skin list
  genshen-skin install 芙宁娜
  genshen-skin show 雷神
  genshen-skin wallpaper furina 2
  genshen-skin pet keqing
  genshen-skin uninstall 芙宁娜

五种等价写法（随便挑一种）
  genshen-skin list
  gss list
  python -m genshen-skin list
  python -m genshen_skin list
  python -m genshen_skins list

文档： https://github.com/WPH666-py/Genshen-Desktop-Skin
"""


def print_commands():
    print(COMMANDS_HELP.rstrip())


def cmd_commands(args):
    print_commands()
    return 0


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(
        prog="genshen-skin",
        description="原神桌面皮肤集合（31 套）：壁纸 / IDE 扩展 / 桌宠 / DSH 插件 一键安装",
        epilog="更多用法见 https://github.com/WPH666-py/Genshen-Desktop-Skin",
    )
    ap.add_argument("-V", "--version", action="version",
                    version="genshen-desktop-skin %s" % __version__)
    ap.add_argument("--mirror", default=None,
                    help="pip 镜像: tuna(清华,默认) | ustc(中科大) | aliyun | tencent | official")
    # 不加 required=True：直接敲 `genshen-skin` 时打印全部命令总览，
    # 而不是甩一个 "the following arguments are required: cmd" 的错误。
    sub = ap.add_subparsers(dest="cmd")

    # 命令总览（不带参数运行也会走到这里）
    p = sub.add_parser("commands", aliases=["help", "?"],
                       help="显示全部命令总览（直接敲 genshen-skin 同效）")
    p.set_defaults(func=cmd_commands)

    sub.add_parser("list", help="列出全部 31 套皮肤").set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="查看某套皮肤的详情")
    p.add_argument("key")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("catalog", help="打印皮肤目录")
    p.add_argument("--json", action="store_true")
    p.add_argument("--md", action="store_true")
    p.set_defaults(func=cmd_catalog)

    sub.add_parser("env", help="检测本机环境（IDE / DSH / 代理 / 屏幕）").set_defaults(func=cmd_env)
    sub.add_parser("doctor", help="体检：代理 / 网络 / 镜像 / git / Pillow").set_defaults(func=cmd_doctor)
    sub.add_parser("paths", help="显示各类本地目录").set_defaults(func=cmd_paths)

    p = sub.add_parser("install", help="一键安装（壁纸 + IDE 扩展 + 桌宠）")
    p.add_argument("key")
    p.add_argument("--mode", default="random", help="壁纸模式: 1/2/3/random（默认 random）")
    p.add_argument("--size", default=None, help="壁纸尺寸，如 2560x1440（默认按屏幕）")
    p.add_argument("--fit", default=None, choices=[wallpaper.FIT_COVER, wallpaper.FIT_CONTAIN, wallpaper.FIT_BLUR],
                   help="适配方式：blur(默认,无黑边) / cover(裁切铺满) / contain(完整留白)")
    p.add_argument("--editor", default=None, help="只装到指定编辑器，如 vscode / trae")
    p.add_argument("--generic", action="store_true", help="桌宠使用内置通用版")
    p.add_argument("--force-pet", action="store_true", help="即使仓库没有桌宠也启动通用桌宠")
    p.add_argument("--no-wallpaper", action="store_true")
    p.add_argument("--no-ide", action="store_true")
    p.add_argument("--no-pet", action="store_true")
    p.add_argument("--no-dsh", action="store_true", help="不提示 DSH 安装步骤")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("wallpaper", help="切换桌面壁纸")
    p.add_argument("key")
    p.add_argument("mode", nargs="?", default="random", help="1/2/3/random")
    p.add_argument("--size", default=None)
    p.add_argument("--fit", default=None, choices=[wallpaper.FIT_COVER, wallpaper.FIT_CONTAIN, wallpaper.FIT_BLUR])
    p.add_argument("--list", action="store_true", help="只列出可用壁纸")
    p.set_defaults(func=cmd_wallpaper)

    p = sub.add_parser("export", help="导出全部壁纸（PyCharm 背景图用）")
    p.add_argument("key")
    p.add_argument("--out", default=None, help="输出目录")
    p.add_argument("--size", default=None)
    p.add_argument("--fit", default=None, choices=[wallpaper.FIT_COVER, wallpaper.FIT_CONTAIN, wallpaper.FIT_BLUR])
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("pet", help="桌面桌宠（启动 / 停止 / 自启 / 卸载）")
    p.add_argument("key")
    p.add_argument("--stop", action="store_true", help="停止桌宠")
    p.add_argument("--generic", action="store_true", help="用内置通用桌宠")
    p.add_argument("--uninstall", action="store_true", help="卸载桌宠（含自启与本地文件）")
    p.add_argument("--autostart", dest="autostart", action="store_true", default=None, help="开启开机自启")
    p.add_argument("--no-autostart", dest="autostart", action="store_false", help="关闭开机自启")
    p.set_defaults(func=cmd_pet)

    p = sub.add_parser("ide", help="安装 VSIX 扩展到 VSCode/Trae/CodeX…")
    p.add_argument("key", nargs="?", default=None)
    p.add_argument("--list", action="store_true", help="列出检测到的编辑器")
    p.add_argument("--editor", default=None, help="只装到指定编辑器")
    p.add_argument("--uninstall", action="store_true", help="卸载扩展")
    p.set_defaults(func=cmd_ide)

    p = sub.add_parser("dsh", help="准备 DeepSeek Harness 动态插件载荷")
    p.add_argument("key")
    p.add_argument("--with-host", action="store_true", help="同时准备全画质 host.js")
    p.add_argument("--json", action="store_true", help="输出 JSON 摘要")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_dsh)

    p = sub.add_parser("deepking", help="导出 DeepKing 皮肤规范包")
    p.add_argument("key")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_deepking)

    p = sub.add_parser("sync", help="克隆皮肤仓库到本地")
    p.add_argument("key", nargs="?", default=None)
    p.add_argument("--all", action="store_true", help="克隆全部 31 套")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("vendor", help="把 31 个仓库全部落地到指定目录（离线收藏）")
    p.add_argument("--out", required=True, help="目标目录")
    p.add_argument("--force", action="store_true", help="已存在也重新拉取")
    p.set_defaults(func=cmd_vendor)

    p = sub.add_parser("mirror", help="显示 / 设置 pip 镜像与 GitHub 加速通道")
    p.add_argument("--set", default=None, help="设为默认: tuna | ustc | aliyun | tencent | official")
    p.set_defaults(func=cmd_mirror)

    p = sub.add_parser("uninstall", help="卸载某套皮肤（扩展 / 桌宠 / 本地副本）")
    p.add_argument("key")
    p.add_argument("--keep-files", action="store_true", help="保留已下载的仓库文件")
    p.set_defaults(func=cmd_uninstall)

    return ap


def main(argv=None):
    prepare_console()
    ap = build_parser()
    args = ap.parse_args(argv)

    # 不带任何参数 → 展示全部命令（这正是「装完包之后想看到什么」）
    if not getattr(args, "cmd", None):
        print_commands()
        return 0

    if args.cmd == "sync" and not args.all and not args.key:
        ap.error("sync 需要 <角色> 或 --all")
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n已中断", file=sys.stderr)
        return 130
    except SystemExit:
        raise
    except Exception as e:
        print("[genshen] 出错: %s" % e, file=sys.stderr)
        if os.environ.get("GENSHEN_DEBUG"):
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
