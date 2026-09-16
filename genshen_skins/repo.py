# -*- coding: utf-8 -*-
"""genshen_skins.repo —— 把皮肤仓库拿到本地。

两条路径：
  * `ensure_repo()`  —— git clone（带代理 + 多个 GitHub 加速前缀，逐个回退）
  * `fetch_raw()`    —— 只取单个文件（DSH 的 client.js、skin.json 等），不需要 git

本地根目录：`~/.genshen-skins/<仓库名>`（可用 GENSHEN_HOME 覆盖）。
所有下载都不改动包自身，全部落在用户目录。
"""
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from . import mirror, proxy

OWNER = "WPH666-py"
BRANCH = "main"
RAW_HOST = "https://raw.githubusercontent.com"
CODELOAD = "https://codeload.github.com"

DEFAULT_HOME = os.path.join(os.path.expanduser("~"), ".genshen-skins")
TIMEOUT = 60
_last_good = {}   # {"clone": 说明, "raw": 说明} —— 记住本次运行中可用的通道


def home_dir():
    return os.path.abspath(os.path.expanduser(os.environ.get("GENSHEN_HOME") or DEFAULT_HOME))


def skin_dir(repo):
    return os.path.join(home_dir(), repo)


def have_git():
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
        return True
    except Exception:
        return False


def is_cloned(path):
    return os.path.isdir(os.path.join(path, ".git"))


# ---------------------------------------------------------------------------
# git clone
# ---------------------------------------------------------------------------
def _run_git(args, **kw):
    return subprocess.run(["git"] + proxy.git_config_args() + args,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, **kw)


def ensure_repo(repo, url=None, quiet=False, update=True):
    """确保 <repo> 已克隆到本地，返回其目录。

    已存在则（默认）做一次 `git pull --ff-only`，这样皮肤仓库更新后本工具能自动跟上。
    克隆失败会依次尝试 GitHub 加速前缀。
    """
    dst = skin_dir(repo)
    url = url or "https://github.com/%s/%s.git" % (OWNER, repo)

    if is_cloned(dst):
        if update:
            env = proxy.env_with_proxy()
            r = _run_git(["-C", dst, "pull", "--ff-only"], timeout=180, env=env)
            if r.returncode != 0 and not quiet:
                # pull 失败不算致命：本地副本仍然可用（离线 / 改动过的工作区）
                print("[genshen] 提示: %s 更新失败，继续使用本地副本" % repo, file=sys.stderr)
        return dst

    if not have_git():
        raise RuntimeError(
            "需要 git 才能克隆皮肤仓库，但本机没找到 git。\n"
            "  Windows : winget install Git.Git\n"
            "  macOS   : brew install git\n"
            "  Ubuntu  : sudo apt install git")

    os.makedirs(home_dir(), exist_ok=True)
    env = proxy.env_with_proxy()
    errors = []
    for label, curl in mirror.clone_candidates(url):
        if not quiet:
            print("[genshen] 克隆 %s  (%s)" % (repo, label))
        if os.path.exists(dst):
            _rmtree(dst)
        r = _run_git(["clone", "--depth", "1", "--branch", BRANCH, curl, dst],
                     timeout=900, env=env)
        if r.returncode == 0 and os.path.isdir(dst):
            _last_good["clone"] = label
            return dst
        errors.append("%s: %s" % (label, (r.stdout or "").strip().splitlines()[-1:] or "失败"))
        if os.path.exists(dst):
            _rmtree(dst)

    # 最后兜底：走 codeload 下载 tarball（不需要 git）
    try:
        if not quiet:
            print("[genshen] git 全部通道失败，改用源码包下载 %s" % repo)
        return download_tarball(repo, dst, quiet=quiet)
    except Exception as e:
        errors.append("源码包: %s" % e)

    raise RuntimeError("无法获取 %s，尝试过的通道：\n  %s" % (repo, "\n  ".join(errors)))


def download_tarball(repo, dst, branch=BRANCH, quiet=False):
    """下载仓库 tarball 并解压到 dst（git 不可用时的兜底）。"""
    last = None
    for label, base in (("codeload", CODELOAD),) + tuple(
            (p["name"], (p["clone"] or "") + CODELOAD) for p in mirror.GITHUB_PROXIES
            if p["clone"]):
        url = "%s/%s/%s/tar.gz/refs/heads/%s" % (base, OWNER, repo, branch)
        try:
            data = _http_get(url, timeout=300)
        except Exception as e:
            last = "%s: %s" % (label, e)
            continue
        tmp = tempfile.mkdtemp(prefix="genshen-")
        tar_path = os.path.join(tmp, "repo.tar.gz")
        with open(tar_path, "wb") as f:
            f.write(data)
        with tarfile.open(tar_path, "r:gz") as tf:
            tf.extractall(tmp)
        inner = [os.path.join(tmp, n) for n in os.listdir(tmp)
                 if os.path.isdir(os.path.join(tmp, n))]
        if not inner:
            last = "%s: 压缩包结构异常" % label
            continue
        if os.path.exists(dst):
            _rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(inner[0], dst)
        _rmtree(tmp)
        _last_good["clone"] = label
        return dst
    raise RuntimeError("源码包下载失败（%s）" % (last or "无可用通道"))


def rmtree(path):
    """删除目录树（Windows 安全版）。

    Windows 上 git 的 pack 文件带**只读**属性（`-ar---`），
    `shutil.rmtree` 遇到它们会抛异常；而 `ignore_errors=True` 又会把异常**静默吞掉**，
    结果是"报告删除成功、目录却还在"，只剩 `.git/objects/pack/*` 一堆残骸 ——
    下次 `git clone` 到同一路径就会失败。所以这里显式清掉只读位再删。
    """
    import shutil as _shutil
    import stat as _stat

    if not path or not os.path.exists(path):
        return True

    def _on_error(func, p, _exc):
        try:
            os.chmod(p, _stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    try:
        _shutil.rmtree(path, onerror=_on_error)
    except Exception:
        pass
    return not os.path.exists(path)


# 兼容旧调用名
_rmtree = rmtree


# ---------------------------------------------------------------------------
# 单文件下载（raw）
# ---------------------------------------------------------------------------
def _http_get(url, timeout=TIMEOUT, want_json=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": "genshen-skin/%s" % _version(),
        "Accept": "application/json" if want_json else "*/*",
    })
    with proxy.opener().open(req, timeout=timeout) as r:
        data = r.read()
    if want_json:
        import json
        return json.loads(data.decode("utf-8"))
    return data


def _version():
    try:
        from . import __version__
        return __version__
    except Exception:
        return "0"


def fetch_raw(repo, path, branch=BRANCH, binary=True, timeout=TIMEOUT):
    """下载皮肤仓库里的单个文件，自动在直连与多个加速通道间回退。

    返回 bytes（binary=True）或 str（binary=False）。全部通道失败抛 RuntimeError。
    """
    quoted = urllib.parse.quote(path)
    errors = []
    good = _last_good.get("raw")
    cands = mirror.raw_candidates(OWNER, repo, branch, quoted)
    if good:
        cands.sort(key=lambda t: 0 if t[0] == good else 1)
    for label, url in cands:
        try:
            data = _http_get(url, timeout=timeout)
        except urllib.error.HTTPError as e:
            errors.append("%s: HTTP %s" % (label, e.code))
            continue
        except Exception as e:
            errors.append("%s: %s" % (label, type(e).__name__))
            continue
        if not data:
            errors.append("%s: 空响应" % label)
            continue
        _last_good["raw"] = label
        return data if binary else data.decode("utf-8", "replace")
    raise RuntimeError("下载 %s/%s 失败，尝试过的通道：\n  %s"
                       % (repo, path, "\n  ".join(errors)))


def fetch_text(repo, path, branch=BRANCH):
    return fetch_raw(repo, path, branch=branch, binary=False)


def fetch_json(repo, path, branch=BRANCH):
    import json
    return json.loads(fetch_text(repo, path, branch=branch))


def download_to(repo, path, dest, branch=BRANCH, quiet=False):
    """把仓库里的文件下载到本地 dest（自动建目录），返回 dest。"""
    data = fetch_raw(repo, path, branch=branch)
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    if not quiet:
        print("[genshen] 下载 %s -> %s (%.1f KB)" % (path, dest, len(data) / 1024.0))
    return dest


def last_good():
    return dict(_last_good)
