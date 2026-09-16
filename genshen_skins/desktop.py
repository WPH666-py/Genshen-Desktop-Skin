# -*- coding: utf-8 -*-
"""genshen_skins.desktop —— Windows 桌面置顶桌宠。

28 套皮肤仓库自带定制版桌宠脚本（含各自的大招特效），本模块直接复用；
没有自带脚本的皮肤（例如刻晴）改用本包内置的**通用桌宠** `genshen-pet.ps1`，
它读同目录的 `pet.json`（由本模块生成），因此任何皮肤都能有桌宠。

桌宠悬浮于一切窗口之上 —— VSCode / PyCharm / Trae / claude-code / kimi-code /
CodeX / Harness 全部适用，这正是"覆盖所有 IDE"的那条路径。
"""
import json
import os
import shutil
import subprocess
import sys

from . import proxy, repo

PET_DIR_NAME = "_pets"
RUN_KEY = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
GENERIC_PS1 = "genshen-pet.ps1"


def pets_home():
    d = os.path.join(repo.home_dir(), PET_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def pet_dir(skin):
    return os.path.join(pets_home(), skin["repo"])


def asset_path(*parts):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", *parts)


def ensure_ps1_bom(path):
    """保证 .ps1 是 UTF-8 **带 BOM**。

    Windows PowerShell 5.1（powershell.exe）在没有 BOM 时按系统 ANSI 代码页
    （简体中文系统 = GBK）解析脚本文件 —— 脚本里的中文与 ✦ 等符号会变成乱码，
    甚至直接解析失败。各皮肤仓库自带的 .ps1 也都是带 BOM 的，这里保持一致。
    """
    try:
        with open(path, "rb") as f:
            raw = f.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            return path
        text = raw.decode("utf-8", "replace")
        with open(path, "wb") as f:
            f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))
    except Exception:
        pass
    return path


def ensure_ps1_bom_text(path, text):
    """把 text 以 UTF-8 + BOM 写进 path（新建脚本时用）。"""
    with open(path, "wb") as f:
        f.write(b"\xef\xbb\xbf" + text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    return path


def is_windows():
    return sys.platform == "win32"


def has_bespoke(skin):
    return bool((skin.get("paths") or {}).get("desktop_ps1"))


# ---------------------------------------------------------------------------
# 准备桌宠目录
# ---------------------------------------------------------------------------
def prepare(skin, generic=False, quiet=False):
    """把桌宠所需文件准备到 ~/.genshen-skins/_pets/<repo>，返回要启动的 ps1 路径。"""
    dst = pet_dir(skin)
    paths = skin.get("paths") or {}
    use_generic = generic or not has_bespoke(skin)

    if not use_generic:
        # 定制版：克隆仓库后把 desktop/ 复制出来
        src_repo = repo.ensure_repo(skin["repo"], url=skin.get("clone"), quiet=quiet)
        src = os.path.join(src_repo, "desktop")
        if not os.path.isdir(src):
            raise RuntimeError("%s 里没有 desktop/ 目录" % skin["repo"])
        if os.path.isdir(dst):
            shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        ps1 = os.path.join(dst, os.path.basename(paths["desktop_ps1"]))
        if not os.path.exists(ps1):
            cand = [f for f in os.listdir(dst) if f.lower().endswith(".ps1")]
            if not cand:
                raise RuntimeError("desktop/ 里没有 .ps1")
            ps1 = os.path.join(dst, cand[0])
        for f in os.listdir(dst):
            if f.lower().endswith(".ps1"):
                ensure_ps1_bom(os.path.join(dst, f))
        if not quiet:
            print("[genshen] 桌宠（%s 定制版）已就绪: %s" % (skin["char"], dst))
        return ps1

    # 通用版：脚本 + pet.json + 壁纸 + 语音
    os.makedirs(dst, exist_ok=True)
    shutil.copy2(asset_path(GENERIC_PS1), os.path.join(dst, GENERIC_PS1))
    ensure_ps1_bom(os.path.join(dst, GENERIC_PS1))

    local = repo.skin_dir(skin["repo"])
    walls, voices = [], []
    for rel in skin.get("wallpapers") or []:
        target = os.path.join(dst, os.path.basename(rel))
        if not os.path.exists(target):
            repo.download_to(skin["repo"], rel, target, quiet=True)
        walls.append(os.path.basename(rel))
    for rel in (skin.get("voices") or [])[:1]:
        target = os.path.join(dst, os.path.basename(rel))
        if not os.path.exists(target):
            repo.download_to(skin["repo"], rel, target, quiet=True)
        voices.append(os.path.basename(rel))

    cfg = {
        "id": skin["id"],
        "char": skin["char"],
        "name": skin["name"],
        "accent": skin.get("accent") or "#7a7f8c",
        "wallpapers": walls,
        "voice": voices[0] if voices else None,
        "repo": skin["repo"],
        "home": local,
    }
    with open(os.path.join(dst, "pet.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    if not quiet:
        print("[genshen] 桌宠（通用版）已就绪: %s  (%d 张壁纸%s)"
              % (dst, len(walls), "、含大招语音" if voices else ""))
    return os.path.join(dst, GENERIC_PS1)


# ---------------------------------------------------------------------------
# 启动 / 停止
# ---------------------------------------------------------------------------
LAUNCHER_BAT = "genshen-launch.bat"


def launcher_bat(skin, ps1=None):
    """生成桌宠的 .bat 启动器（总是由我们自己生成，保证行为一致）。

    两个要点：
      * `-WindowStyle Hidden` —— 否则 powershell 会附带一个黑色控制台窗口，
        既难看又会挡住桌宠；
      * 通过 explorer.exe 打开这个 .bat 来启动（见 `launch()`）—— explorer 常驻
        用户会话、不在调用者的 Job 对象里，桌宠因此不会随调用方进程树被回收。

    命名用 ASCII 的 genshen-launch.bat，避免与各皮肤仓库自带的
    `启动-XX皮肤.bat` 撞名（那些没有 -WindowStyle Hidden）。
    """
    dst = pet_dir(skin)
    if ps1 is None:
        cands = [f for f in os.listdir(dst) if f.lower().endswith(".ps1")]
        ps1 = os.path.join(dst, cands[0]) if cands else None
    if not ps1:
        return None
    bat = os.path.join(dst, LAUNCHER_BAT)
    # 注意 %%~dp0：这里是 Python 的 %-格式化字符串，%% 才会得到批处理的 %~dp0
    body = ("@echo off\r\n"
            'start "" powershell.exe -NoProfile -WindowStyle Hidden '
            '-STA -ExecutionPolicy Bypass -File "%%~dp0%s"\r\n' % os.path.basename(ps1))
    with open(bat, "w", encoding="ascii", errors="replace", newline="") as f:
        f.write(body)
    return bat


def launch(skin, generic=False, quiet=False):
    if not is_windows():
        raise RuntimeError("桌面桌宠目前仅支持 Windows；DSH 插件与 VSCode 扩展跨平台可用")
    ps1 = prepare(skin, generic=generic, quiet=quiet)
    bat = launcher_bat(skin, ps1)

    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    real = None

    # 首选：交给 explorer.exe 打开 .bat。
    # 为什么不用直接 CreateProcess：很多宿主（IDE 终端、AI Agent 的一次命令执行）
    # 会给子进程建 Job 对象，命令结束就把整棵树杀掉；而 Job 通常不允许 breakaway，
    # 直接启动的桌宠刚起来就被带走。explorer 不在那个 Job 里，由它来起就没这个问题。
    if bat:
        try:
            subprocess.Popen(["explorer.exe", bat], creationflags=CREATE_NO_WINDOW)
            real = _capture_pid(skin, tries=12, delay=0.7)
        except Exception:
            real = None

    # 兜底：直接启动（自带 breakaway 尝试）
    if not real:
        cmd = ["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass",
               "-WindowStyle", "Hidden", "-File", ps1]
        DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        CREATE_BREAKAWAY_FROM_JOB = 0x01000000
        base = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        proc = None
        for flags in (base | CREATE_BREAKAWAY_FROM_JOB, base, 0):
            try:
                proc = subprocess.Popen(cmd, creationflags=flags)
                break
            except OSError:
                continue
        if proc is None:
            raise RuntimeError("无法启动桌宠进程")
        real = _capture_pid(skin, tries=8, delay=0.7)

    if not quiet:
        if real:
            print("[genshen] %s 桌宠已启动（PID %d，右下角悬浮，可拖动；点击释放大招，右键菜单换壁纸/卸载）"
                  % (skin["char"], real))
        else:
            print("[genshen] %s 桌宠已启动（进程仍在初始化；若右下角始终没出现，"
                  "请检查是否被安全软件拦截）" % skin["char"])
    return ps1


def pid_file(skin):
    return os.path.join(pet_dir(skin), ".pid")


def _write_pid(skin, pid):
    try:
        with open(pid_file(skin), "w", encoding="utf-8") as f:
            f.write(str(pid))
    except Exception:
        pass


def _read_pid(skin):
    try:
        with open(pid_file(skin), encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def _capture_pid(skin, tries=8, delay=0.7, quiet=True):
    """启动后把真正的桌宠 PID 记下来。

    为什么要扫描而不是直接用 `Popen().pid`：Windows 上用 DETACHED_PROCESS
    启动 powershell.exe 时，CreateProcess 返回的 PID **不是**最终那个拥有
    窗口的进程（实测两者不同），拿它去判活会一直判成"没在运行"。
    这里改为回扫真实进程，通用桌宠脚本自己也会写一份 .pid，两边互为印证。
    """
    import time
    # 通用桌宠脚本启动时会自己写 .pid（最准也最快），先看它
    for _ in range(max(1, tries)):
        pid = _read_pid(skin)
        if pid and _pid_alive(pid):
            return pid
        pids = _find_pet_pids(skin)
        if pids:
            _write_pid(skin, pids[0])
            return pids[0]
        time.sleep(delay)
    return None


def _pid_alive(pid):
    """该 PID 是否还是一个活着的 PowerShell 进程。

    用 ctypes 直接问内核（OpenProcess + WaitForSingleObject），**不起子进程**：
      * `os.kill(pid, 0)` 在 Windows 上会真的 TerminateProcess，绝不能用；
      * `powershell -Command "..."` 要嵌套三层引号，Windows 命令行解析会把
        `\\"` 传坏，导致扫描结果莫名其妙为空（踩过这个坑）。
    """
    if not is_windows() or not pid:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        SYNCHRONIZE = 0x00100000
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        WAIT_TIMEOUT = 0x00000102
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        h = k32.OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not h:
            return False
        try:
            if k32.WaitForSingleObject(wintypes.HANDLE(h), 0) != WAIT_TIMEOUT:
                return False        # 已退出
            # 再确认它确实是 PowerShell，防止 PID 被系统复用
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if k32.QueryFullProcessImageNameW(wintypes.HANDLE(h), 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower() in ("powershell.exe", "pwsh.exe")
            return True
        finally:
            k32.CloseHandle(wintypes.HANDLE(h))
    except Exception:
        return False


_SCAN_PS1 = r"""param([Parameter(Mandatory=$true)][string]$Dir)
# 只认真正的桌宠进程：命令行里带目标目录、带 -File、且指向 .ps1。
# 排除 $PID 自己 —— 否则扫描脚本会把自身算进去，running() 永远为真。
Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" |
  Where-Object {
    $_.ProcessId -ne $PID -and
    $_.CommandLine -and
    $_.CommandLine.Contains($Dir) -and
    $_.CommandLine -match '-File' -and
    $_.CommandLine -match '\.ps1'
  } |
  Select-Object -ExpandProperty ProcessId
"""


def _find_pet_pids(skin):
    """扫描正在运行的该皮肤桌宠 PID（用于识别用户双击 .bat 启动的桌宠）。

    脚本先落到临时 .ps1 再用 `-File` 执行 —— 避免 `-Command` 里路径与
    引号嵌套被 Windows 命令行解析破坏。
    """
    if not is_windows():
        return []
    tmp = None
    try:
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="genshen-scan-")
        os.close(fd)
        ensure_ps1_bom_text(tmp, _SCAN_PS1)
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass",
             "-File", tmp, "-Dir", pet_dir(skin)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=40)
        return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]
    except Exception:
        return []
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except Exception:
                pass


def stop(skin, quiet=False):
    pids = set(_find_pet_pids(skin))
    pid = _read_pid(skin)
    if pid and _pid_alive(pid):
        pids.add(pid)
    pids = sorted(pids)
    try:
        os.remove(pid_file(skin))
    except Exception:
        pass
    if not pids:
        if not quiet:
            print("[genshen] %s 桌宠没有在运行" % skin["char"])
        return 0
    for p in pids:
        subprocess.call(["taskkill", "/PID", str(p), "/F"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not quiet:
        print("[genshen] 已停止 %s 桌宠（%d 个进程）" % (skin["char"], len(pids)))
    return len(pids)


def running(skin):
    """桌宠是否在运行。

    先看启动时记下的 .pid，再回扫进程；两者都没有就把过期的 .pid 清掉。
    通用桌宠脚本启动时也会自己写一份 .pid（见 genshen-pet.ps1）。
    """
    pid = _read_pid(skin)
    if pid and _pid_alive(pid):
        return True
    live = _find_pet_pids(skin)
    if live:
        _write_pid(skin, live[0])
        return True
    try:
        os.remove(pid_file(skin))
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# 开机自启
# ---------------------------------------------------------------------------
def _run_value_name(skin):
    return "GenshenSkin_%s" % skin["id"]


def set_autostart(skin, enable=True, generic=False, quiet=False):
    if not is_windows():
        return False, "开机自启目前仅支持 Windows"
    name = _run_value_name(skin)
    if not enable:
        cmd = ("Remove-ItemProperty -Path '%s' -Name '%s' -ErrorAction SilentlyContinue"
               % (RUN_KEY, name))
        subprocess.call(["powershell.exe", "-NoProfile", "-Command", cmd],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "已关闭 %s 的开机自启" % skin["char"]
    ps1 = prepare(skin, generic=generic, quiet=True)
    value = ('powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%s"' % ps1)
    cmd = ("Set-ItemProperty -Path '%s' -Name '%s' -Value \"%s\" -Type String"
           % (RUN_KEY, name, value.replace('"', '\\"')))
    r = subprocess.call(["powershell.exe", "-NoProfile", "-Command", cmd],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r == 0:
        return True, "已开启 %s 的开机自启" % skin["char"]
    return False, "写入注册表失败"


def has_autostart(skin):
    if not is_windows():
        return False
    cmd = ("(Get-ItemProperty -Path '%s' -Name '%s' -ErrorAction SilentlyContinue).'%s'"
           % (RUN_KEY, _run_value_name(skin), _run_value_name(skin)))
    try:
        r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           text=True, timeout=30)
        return bool((r.stdout or "").strip())
    except Exception:
        return False


def uninstall(skin, quiet=False):
    """停止桌宠、移除自启、删除桌宠目录。"""
    stop(skin, quiet=True)
    set_autostart(skin, False, quiet=True)
    d = pet_dir(skin)
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
    if not quiet:
        print("[genshen] 已卸载 %s 桌宠（含开机自启与本地文件）" % skin["char"])
    return True
