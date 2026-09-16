# -*- coding: utf-8 -*-
"""genshen_skins.targets —— 识别本机的 IDE / 编辑器，并把皮肤装进去。

覆盖用户点名的全部环境：

    VSCode · Trae · CodeX · Cursor · Windsurf · VSCodium   —— VSIX 扩展
    PyCharm · IntelliJ · WebStorm · GoLand …               —— 背景图 + 壁纸导出
    DeepSeek Harness                                       —— 动态 Cordis 插件（见 dsh.py）
    claude-code / kimi-code / CodeX CLI / 任意桌面          —— 桌面置顶桌宠（见 desktop.py）
    DeepKing                                               —— skin.json + CSS 变量规范包

即便某个编辑器没有 CLI，也会退回到"解压 VSIX 到扩展目录"的方式安装。
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

# ---------------------------------------------------------------------------
# VS Code 系编辑器（都吃 .vsix）
#   cli    —— 可执行文件名（PATH 中查找）
#   dirs   —— 扩展目录（相对于用户主目录）
#   win    —— Windows 上常见的绝对路径（支持 %LOCALAPPDATA% 展开）
# ---------------------------------------------------------------------------
VSCODE_LIKE = (
    {
        "id": "vscode", "name": "VSCode", "cli": ("code", "code.cmd"),
        "dirs": (".vscode/extensions",),
        "win": (r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd",
                r"%PROGRAMFILES%\Microsoft VS Code\bin\code.cmd"),
    },
    {
        "id": "trae", "name": "Trae", "cli": ("trae", "trae.cmd"),
        "dirs": (".trae/extensions", ".trae-cn/extensions"),
        "win": (r"%LOCALAPPDATA%\Programs\Trae\bin\trae.cmd",
                r"%LOCALAPPDATA%\Trae\bin\trae.cmd",
                r"%LOCALAPPDATA%\Programs\Trae CN\bin\trae.cmd"),
    },
    {
        "id": "codex", "name": "CodeX", "cli": ("codex", "codex.cmd"),
        "dirs": (".codex/extensions", ".codex-ide/extensions"),
        "win": (r"%LOCALAPPDATA%\Programs\CodeX\bin\codex.cmd",
                r"%LOCALAPPDATA%\CodeX\bin\codex.cmd"),
    },
    {
        "id": "cursor", "name": "Cursor", "cli": ("cursor", "cursor.cmd"),
        "dirs": (".cursor/extensions",),
        "win": (r"%LOCALAPPDATA%\Programs\cursor\resources\app\bin\cursor.cmd",),
    },
    {
        "id": "windsurf", "name": "Windsurf", "cli": ("windsurf", "windsurf.cmd"),
        "dirs": (".windsurf/extensions",),
        "win": (r"%LOCALAPPDATA%\Programs\Windsurf\bin\windsurf.cmd",),
    },
    {
        "id": "vscodium", "name": "VSCodium", "cli": ("codium", "codium.cmd"),
        "dirs": (".vscode-oss/extensions",),
        "win": (r"%LOCALAPPDATA%\Programs\VSCodium\bin\codium.cmd",),
    },
)

JETBRAINS_HINTS = ("pycharm", "idea", "webstorm", "goland", "clion", "phpstorm", "rider", "datagrip")


def _expand(p):
    return os.path.expandvars(os.path.expanduser(p))


def _which(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def _ext_dir(editor):
    home = os.path.expanduser("~")
    for d in editor["dirs"]:
        p = os.path.join(home, d.replace("/", os.sep))
        if os.path.isdir(p):
            return p
    return os.path.join(home, editor["dirs"][0].replace("/", os.sep))


def detect_editors():
    """返回本机装了的 VS Code 系编辑器：{id,name,cli,extdir,how}。"""
    found = []
    for ed in VSCODE_LIKE:
        cli = _which(ed["cli"])
        if not cli and sys.platform == "win32":
            for cand in ed.get("win", ()):
                p = _expand(cand)
                if os.path.exists(p):
                    cli = p
                    break
        extdir = _ext_dir(ed)
        has_dir = os.path.isdir(extdir) or os.path.isdir(os.path.dirname(extdir))
        if cli or has_dir:
            found.append({
                "id": ed["id"], "name": ed["name"], "cli": cli,
                "extdir": extdir, "how": "cli" if cli else "unzip",
            })
    return found


def find_editor(name):
    """按 id / 名称找个编辑器（大小写不敏感）。"""
    if not name:
        return None
    n = name.strip().lower()
    for ed in detect_editors():
        if n in (ed["id"], ed["name"].lower()):
            return ed
    # 用户可能写 vscode/trae/codex 之外的别名
    alias = {"vs code": "vscode", "code": "vscode", "pycharm": "vscode"}.get(n)
    if alias:
        for ed in detect_editors():
            if ed["id"] == alias:
                return ed
    return None


def detect_jetbrains():
    """返回本机 JetBrains 系 IDE 列表（含 PyCharm）。"""
    found = []
    home = os.path.expanduser("~")

    if sys.platform == "win32":
        cands = []
        for base in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("PROGRAMFILES", ""),
                     os.environ.get("PROGRAMFILES(X86)", "")):
            if base:
                cands += glob.glob(os.path.join(base, "*JetBrains*", "*", "bin", "*64.exe"))
                cands += glob.glob(os.path.join(base, "JetBrains", "*", "bin", "*64.exe"))
        for c in cands:
            low = os.path.basename(c).lower()
            if any(h in low for h in JETBRAINS_HINTS) or "64.exe" in low:
                found.append({"name": os.path.basename(os.path.dirname(os.path.dirname(c))),
                              "exe": c})
    elif sys.platform == "darwin":
        for app in glob.glob("/Applications/*.app"):
            low = os.path.basename(app).lower()
            if any(h in low for h in JETBRAINS_HINTS):
                found.append({"name": os.path.basename(app)[:-4], "exe": app})
    else:
        for cand in ("/usr/bin", "/usr/local/bin", "/opt", os.path.join(home, ".local/bin")):
            for f in glob.glob(os.path.join(cand, "*")):
                low = os.path.basename(f).lower()
                if any(h in low for h in JETBRAINS_HINTS):
                    found.append({"name": os.path.basename(f), "exe": f})

    # Toolbox 配置目录（即使找不到可执行文件，也说明装过）
    for d in ("~/.config/JetBrains", "~/AppData/Roaming/JetBrains", "~/Library/Application Support/JetBrains"):
        p = _expand(d)
        if os.path.isdir(p):
            for name in sorted(os.listdir(p)):
                if any(h in name.lower() for h in JETBRAINS_HINTS):
                    if not any(f["name"] == name for f in found):
                        found.append({"name": name, "exe": None})
    seen, out = set(), []
    for f in found:
        if f["name"] not in seen:
            seen.add(f["name"])
            out.append(f)
    return out


# ---------------------------------------------------------------------------
# VSIX 安装
# ---------------------------------------------------------------------------
def vsix_extension_id(vsix_path):
    """从 .vsix 里读出扩展 ID（publisher.name）。读不到返回 None。"""
    try:
        with zipfile.ZipFile(vsix_path) as z:
            with z.open("extension/package.json") as f:
                pkg = json.loads(f.read().decode("utf-8", "replace"))
        pub, name = pkg.get("publisher"), pkg.get("name")
        return "%s.%s" % (pub, name) if pub and name else None
    except Exception:
        return None


def install_vsix(editor, vsix_path, quiet=False):
    """把 vsix 装进编辑器。返回 (是否成功, 说明)。"""
    if not os.path.exists(vsix_path):
        return False, "找不到 VSIX: %s" % vsix_path

    if editor.get("cli"):
        cmd = [editor["cli"], "--install-extension", vsix_path, "--force"]
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=300)
            if r.returncode == 0:
                return True, "已通过 %s 安装" % editor["name"]
            note = (r.stdout or "").strip().splitlines()[-1:]
            note = note[0] if note else "退出码 %d" % r.returncode
        except Exception as e:
            note = str(e)
        if not quiet:
            print("[genshen] %s CLI 安装失败(%s)，改用手动解压" % (editor["name"], note))

    # 退路：把 VSIX（本身是 zip）解压到扩展目录
    ext_id = vsix_extension_id(vsix_path)
    if not ext_id:
        return False, "无法读取 VSIX 内的扩展 ID"
    exts = editor.get("extdir")
    if not exts:
        return False, "找不到 %s 的扩展目录" % editor["name"]
    target = os.path.join(exts, ext_id)
    try:
        os.makedirs(exts, exist_ok=True)
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        tmp = tempfile.mkdtemp(prefix="genshen-vsix-")
        with zipfile.ZipFile(vsix_path) as z:
            z.extractall(tmp)
        src = os.path.join(tmp, "extension")
        if not os.path.isdir(src):
            return False, "VSIX 结构异常（缺少 extension/）"
        shutil.move(src, target)
        shutil.rmtree(tmp, ignore_errors=True)
        return True, "已解压到 %s（重启 %s 生效）" % (target, editor["name"])
    except Exception as e:
        return False, "解压失败: %s" % e


def uninstall_vsix(editor, ext_id, quiet=False):
    """卸载扩展。"""
    if editor.get("cli"):
        try:
            r = subprocess.run([editor["cli"], "--uninstall-extension", ext_id],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=180)
            if r.returncode == 0:
                return True, "已通过 %s 卸载" % editor["name"]
        except Exception:
            pass
    exts = editor.get("extdir")
    if exts:
        target = os.path.join(exts, ext_id)
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
            return True, "已删除 %s" % target
    return False, "未能卸载 %s" % ext_id


def installed_vsix_editors(ext_id):
    """返回已装过该扩展的编辑器列表。"""
    out = []
    for ed in detect_editors():
        exts = ed.get("extdir")
        if not exts:
            continue
        # CLI 装的会带版本后缀：publisher.name-1.0.0
        if glob.glob(os.path.join(exts, ext_id + "*")):
            out.append(ed)
    return out


# ---------------------------------------------------------------------------
# DeepSeek Harness 检测
# ---------------------------------------------------------------------------
def detect_dsh():
    """判断当前是否运行在 DeepSeek Harness 里；返回 (是否, 说明)。"""
    envs = {k: v for k, v in os.environ.items() if k.startswith("DSH")}
    if envs:
        home = envs.get("DSH_HOME") or ""
        return True, "检测到 DSH 环境变量%s" % (" (DSH_HOME=%s)" % home if home else "")
    return False, "未检测到 DSH 环境变量"


def detect_agent_cli():
    """识别当前 AI 助手环境（claude-code / kimi-code / codex / trae 等）。"""
    hits = []
    mapping = {
        "claude": "claude-code", "kimi": "kimi-code", "codex": "CodeX",
        "trae": "Trae", "cursor": "Cursor", "aider": "Aider", "gemini": "Gemini CLI",
        "qwen": "Qwen Code", "opencode": "opencode",
    }
    keys = " ".join(os.environ.keys()).lower()
    vals = " ".join(str(v) for v in os.environ.values() if v and len(str(v)) < 260).lower()
    for needle, label in mapping.items():
        if needle in keys or needle in vals:
            hits.append(label)
    if not hits:
        for n in ("claude", "kimi", "codex", "gemini", "qwen", "opencode", "aider"):
            if shutil.which(n):
                hits.append(mapping.get(n, n))
    return sorted(set(hits))


def describe_env():
    """汇总本机环境，供 `genshen-skin env` 与 AI 判断使用。"""
    from . import proxy as _proxy
    from . import wallpaper as _wallpaper

    dsh, dsh_note = detect_dsh()
    url, source = _proxy.detect(force=True)
    try:
        w, h = _wallpaper.screen_size()
    except Exception:
        w, h = 0, 0
    return {
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "python_exe": sys.executable,
        "git": shutil.which("git"),
        "screen": [w, h],
        "pillow": _wallpaper.have_pillow(),
        "proxy": {"url": url, "source": source},
        "dsh": {"detected": dsh, "note": dsh_note},
        "agent_cli": detect_agent_cli(),
        "editors": detect_editors(),
        "jetbrains": detect_jetbrains(),
        "home": os.path.expanduser("~"),
    }
