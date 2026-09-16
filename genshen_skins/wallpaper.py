# -*- coding: utf-8 -*-
"""genshen_skins.wallpaper —— 合成并设置桌面壁纸（跨平台）。

流程：从皮肤仓库取 `-web.jpg` 壁纸 → 按屏幕分辨率适配（可裁切 / 留白 / 模糊填充）
→ 保存到 `~/.genshen-skins/_wallpapers/` → 调用各平台的系统 API 设为壁纸。

Pillow 只在"需要合成"时才是必需的；直接把原图设为壁纸不需要 Pillow。
缺失时会按 `mirror` 选定的源（默认清华）自动安装 —— 这也正是国内网络的稳妥路径。
"""
import os
import shutil
import subprocess
import sys

from . import mirror, proxy, repo

WALL_DIR_NAME = "_wallpapers"

# 适配方式
FIT_COVER = "cover"     # 铺满（超出部分裁掉）—— 默认，最像"壁纸"
FIT_CONTAIN = "contain"  # 完整显示（两侧/上下留白）—— 保持立绘完整
FIT_BLUR = "blur"       # 完整显示 + 背景用放大模糊填满（无黑边）


def wall_dir():
    d = os.path.join(repo.home_dir(), WALL_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# 屏幕尺寸
# ---------------------------------------------------------------------------
def screen_size():
    """返回主屏 (宽, 高)。拿不到就退回 1920x1080。"""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)   # PER_MONITOR_AWARE
            except Exception:
                try:
                    user32.SetProcessDPIAware()
                except Exception:
                    pass
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            if w > 0 and h > 0:
                return int(w), int(h)
        except Exception:
            pass
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        if w > 0 and h > 0:
            return int(w), int(h)
    except Exception:
        pass
    return 1920, 1080


def parse_size(text):
    if not text:
        return None
    try:
        w, h = str(text).lower().replace("×", "x").split("x")
        return int(w), int(h)
    except Exception:
        raise ValueError("尺寸格式应为 1920x1080，收到 %r" % text)


# ---------------------------------------------------------------------------
# 设为系统壁纸
# ---------------------------------------------------------------------------
def set_wallpaper(path):
    """把 path 设为当前桌面壁纸。返回 True/False（不支持时 False）。"""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise IOError("壁纸文件不存在: %s" % path)

    if sys.platform == "win32":
        import ctypes
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        ok = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
        return bool(ok)

    if sys.platform == "darwin":
        script = ('tell application "System Events" to tell every desktop to '
                  'set picture to POSIX file "%s"' % path)
        return subprocess.call(["osascript", "-e", script]) == 0

    # Linux：逐个桌面环境尝试
    uri = "file://%s" % path
    attempts = [
        ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri],
        ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri],
        ["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/workspace0/last-image",
         "-s", path],
        ["feh", "--bg-fill", path],
        ["nitrogen", "--set-zoom-fill", "--save", path],
    ]
    for cmd in attempts:
        if shutil.which(cmd[0]):
            try:
                if subprocess.call(cmd, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL) == 0:
                    return True
            except Exception:
                continue
    return False


# ---------------------------------------------------------------------------
# Pillow：按需安装（走选定镜像）
# ---------------------------------------------------------------------------
def have_pillow():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def ensure_pillow(mirror_name=None, quiet=False):
    """确保 Pillow 可用；缺失时 pip 安装（默认走清华源 + 代理）。"""
    if have_pillow():
        return True
    mirror_name = mirror_name or os.environ.get("GENSHEN_MIRROR") or "tuna"
    args = [sys.executable, "-m", "pip", "install", "--user"]
    args += mirror.pip_install_args(mirror_name)
    args += proxy.pip_args()
    args += ["pillow"]
    if not quiet:
        print("[genshen] 未检测到 Pillow，正在安装：%s" % " ".join(args[2:]))
    try:
        subprocess.check_call(args, env=proxy.env_with_proxy())
    except subprocess.CalledProcessError:
        if not quiet:
            print("[genshen] Pillow 安装失败。请手动执行：\n"
                  "  %s -m pip install -i %s pillow"
                  % (sys.executable, mirror.pip_index(mirror_name)["index"]), file=sys.stderr)
        return False
    import importlib
    importlib.invalidate_caches()
    return have_pillow()


# ---------------------------------------------------------------------------
# 合成
# ---------------------------------------------------------------------------
def compose(src, dest, size=None, fit=FIT_COVER, pad_color=(18, 20, 28)):
    """把单张图按 size 适配后存为 JPEG。返回 dest。

    cover   —— 等比放大到铺满，多余裁掉（默认，最像壁纸）
    contain —— 等比缩小到完整可见，四周填 pad_color
    blur    —— 完整可见，背景用同图放大模糊填满（无黑边，推荐用于立绘）
    """
    from PIL import Image, ImageFilter

    size = size or screen_size()
    img = Image.open(src)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    W, H = size
    sw, sh = img.size

    if fit == FIT_BLUR:
        scale = max(W / float(sw), H / float(sh))
        bg = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))), Image.LANCZOS)
        left = max(0, (bg.size[0] - W) // 2)
        top = max(0, (bg.size[1] - H) // 2)
        bg = bg.crop((left, top, left + W, top + H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=max(12, min(W, H) // 40)))
        bg = bg.point(lambda v: int(v * 0.72))          # 压暗，让前景主体更突出

        scale = min(W / float(sw), H / float(sh))
        fw, fh = max(1, int(sw * scale)), max(1, int(sh * scale))
        fg = img.resize((fw, fh), Image.LANCZOS)
        bg.paste(fg, ((W - fw) // 2, (H - fh) // 2))
        out = bg

    elif fit == FIT_CONTAIN:
        scale = min(W / float(sw), H / float(sh))
        fw, fh = max(1, int(sw * scale)), max(1, int(sh * scale))
        canvas = Image.new("RGB", (W, H), pad_color)
        canvas.paste(img.resize((fw, fh), Image.LANCZOS), ((W - fw) // 2, (H - fh) // 2))
        out = canvas

    else:  # cover
        scale = max(W / float(sw), H / float(sh))
        nw, nh = max(W, int(sw * scale)), max(H, int(sh * scale))
        resized = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - W) // 2
        top = (nh - H) // 2
        out = resized.crop((left, top, left + W, top + H))

    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    out.save(dest, "JPEG", quality=92, optimize=True)
    return dest


def wallpapers_of(skin):
    """返回该皮肤在仓库里的壁纸相对路径列表。"""
    return list(skin.get("wallpapers") or [])


def pick_mode(skin, mode):
    """把模式解析成 (第几张从0起, 说明)。mode: 1/2/3 | random | first。"""
    n = len(wallpapers_of(skin)) or 1
    m = str(mode or "random").strip().lower()
    if m in ("", "random", "r"):
        import random
        idx = random.randrange(n)
        return idx, "随机第 %d 张" % (idx + 1)
    if m in ("first", "默认"):
        return 0, "第 1 张"
    if m.isdigit():
        idx = int(m) - 1
        if idx < 0:
            raise ValueError("壁纸序号从 1 开始")
        if idx >= n:
            raise ValueError("这套皮肤只有 %d 张壁纸，收到第 %d 张" % (n, idx + 1))
        return idx, "第 %d 张" % (idx + 1)
    raise ValueError("未知的壁纸模式 %r（可用：1..%d / random）" % (mode, n))


def ensure_local_assets(skin, quiet=False):
    """把该皮肤的壁纸文件落到本地。优先用已克隆的仓库，否则按需下载单文件。"""
    local = repo.skin_dir(skin["repo"])
    paths = wallpapers_of(skin)
    missing = [p for p in paths if not os.path.exists(os.path.join(local, p))]
    if not missing:
        return local
    if repo.is_cloned(local):
        # 仓库在但缺文件：拉一次更新
        repo.ensure_repo(skin["repo"], url=skin.get("clone"), quiet=quiet)
        return local
    # 只下载需要的壁纸，不克隆整个仓库（省流量，尤其对 19 MB 的仓库）
    for p in missing:
        repo.download_to(skin["repo"], p, os.path.normpath(os.path.join(local, p)), quiet=quiet)
    return local


def apply_skin_wallpaper(skin, mode="random", size=None, fit=FIT_BLUR,
                         mirror_name=None, quiet=False):
    """合成并设置某套皮肤的壁纸，返回生成的壁纸文件路径。"""
    if not ensure_pillow(mirror_name, quiet=quiet):
        raise RuntimeError("缺少 Pillow，无法合成壁纸。请先 pip install pillow")
    local = ensure_local_assets(skin, quiet=quiet)
    walls = wallpapers_of(skin)
    if not walls:
        raise RuntimeError("%s 在 catalog 里没有登记壁纸" % skin["id"])
    idx, label = pick_mode(skin, mode)
    src = os.path.normpath(os.path.join(local, walls[idx]))

    W, H = size or screen_size()
    dest = os.path.join(wall_dir(), "%s-%d-%dx%d.jpg" % (skin["id"], idx + 1, W, H))
    compose(src, dest, size=(W, H), fit=fit)
    ok = set_wallpaper(dest)
    if not quiet:
        print("[genshen] %s 壁纸已生成: %s  (%s / %s)" % (skin["name"], dest, label, fit))
        if not ok:
            print("[genshen] 提示: 未能自动设置系统壁纸，请手动选择上面这个文件", file=sys.stderr)
    return dest


def export_all(skin, out_dir=None, size=None, fit=FIT_BLUR, mirror_name=None, quiet=False):
    """把该皮肤的所有壁纸导出成适配屏幕的 JPEG，返回文件列表（给 PyCharm 等用）。"""
    if not ensure_pillow(mirror_name, quiet=quiet):
        raise RuntimeError("缺少 Pillow，无法导出壁纸。请先 pip install pillow")
    local = ensure_local_assets(skin, quiet=quiet)
    out_dir = os.path.abspath(out_dir or os.path.join(local, "wallpapers"))
    os.makedirs(out_dir, exist_ok=True)
    W, H = size or screen_size()
    made = []
    for i, rel in enumerate(wallpapers_of(skin), 1):
        src = os.path.normpath(os.path.join(local, rel))
        if not os.path.exists(src):
            continue
        dest = os.path.join(out_dir, "%s-%d-%dx%d.jpg" % (skin["id"], i, W, H))
        compose(src, dest, size=(W, H), fit=fit)
        made.append(dest)
        if not quiet:
            print("[genshen] 导出 %s" % dest)
    return made
