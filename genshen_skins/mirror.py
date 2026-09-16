# -*- coding: utf-8 -*-
"""genshen_skins.mirror —— 国内镜像：pip 源 + GitHub 加速。

两类镜像，用途不同，别混：

1. **PyPI 镜像（清华 / 中科大 / 阿里）** —— 只用于 `pip install`。
   清华和 USTC 都是 PyPI 的只读镜像，会自动从 pypi.org 同步；用户不能往镜像
   "上传"包，只能发到 PyPI 后等镜像同步（清华通常几分钟内）。

2. **GitHub 加速（jsDelivr / ghfast / gitmirror …）** —— 用于 clone 皮肤仓库、
   下载 raw 文件。国内直连 raw.githubusercontent.com 经常超时，这些前缀可用。

所有候选按顺序尝试，第一个成功的即被记住（同一次运行内不再重试坏掉的通道）。
"""
import os

# ---------------------------------------------------------------------------
# PyPI 镜像
# ---------------------------------------------------------------------------
PIP_MIRRORS = {
    "tuna": {
        "name": "清华大学 TUNA",
        "index": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "trusted": "pypi.tuna.tsinghua.edu.cn",
        "web": "https://pypi.tuna.tsinghua.edu.cn/simple/genshen-desktop-skin/",
    },
    "ustc": {
        "name": "中国科学技术大学 USTC",
        "index": "https://mirrors.ustc.edu.cn/pypi/simple",
        "trusted": "mirrors.ustc.edu.cn",
        "web": "https://mirrors.ustc.edu.cn/pypi/simple/genshen-desktop-skin/",
    },
    "aliyun": {
        "name": "阿里云",
        "index": "https://mirrors.aliyun.com/pypi/simple",
        "trusted": "mirrors.aliyun.com",
        "web": "https://mirrors.aliyun.com/pypi/simple/genshen-desktop-skin/",
    },
    "tencent": {
        "name": "腾讯云",
        "index": "https://mirrors.cloud.tencent.com/pypi/simple",
        "trusted": "mirrors.cloud.tencent.com",
        "web": "https://mirrors.cloud.tencent.com/pypi/simple/genshen-desktop-skin/",
    },
    "official": {
        "name": "PyPI 官方",
        "index": "https://pypi.org/simple",
        "trusted": None,
        "web": "https://pypi.org/project/genshen-desktop-skin/",
    },
}

MIRROR_ORDER = ("tuna", "ustc", "aliyun", "tencent")

# ---------------------------------------------------------------------------
# GitHub 加速前缀
#   kind="clone" 用于 git clone（前缀 + 完整 https://github.com/... 地址）
#   kind="raw"   用于下载单个文件
# ---------------------------------------------------------------------------
GITHUB_PROXIES = (
    # 直连优先：能连上就走直连，最快也最可信
    {"id": "direct", "name": "直连 GitHub", "clone": "", "raw": ""},
    {"id": "jsdelivr", "name": "jsDelivr CDN",
     "clone": None,  # jsDelivr 不支持 git clone
     "raw": "https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{path}"},
    {"id": "ghfast", "name": "ghfast.top",
     "clone": "https://ghfast.top/", "raw": "https://ghfast.top/"},
    {"id": "gitmirror", "name": "gitmirror",
     "clone": "https://hub.gitmirror.com/", "raw": "https://raw.gitmirror.com/"},
    {"id": "ghproxy", "name": "gh-proxy.com",
     "clone": "https://gh-proxy.com/", "raw": "https://gh-proxy.com/"},
    {"id": "ghproxy_net", "name": "ghproxy.net",
     "clone": "https://ghproxy.net/", "raw": "https://ghproxy.net/"},
)

RAW_HOST = "https://raw.githubusercontent.com"


def pip_index(name):
    return PIP_MIRRORS.get(name, PIP_MIRRORS["official"])


def pip_install_args(name, python=None):
    """构造 `pip install -i <镜像>` 的参数；official 时返回空列表。"""
    m = pip_index(name)
    if name == "official":
        return []
    args = ["-i", m["index"]]
    if m.get("trusted"):
        args += ["--trusted-host", m["trusted"]]
    return args


def clone_url(github_url, proxy):
    """把 https://github.com/o/r.git 套上前缀。"""
    prefix = proxy.get("clone")
    if prefix is None:      # 该通道不支持 clone
        return None
    return prefix + github_url


def raw_url(owner, repo, branch, path, proxy):
    """按通道构造 raw 下载地址。path 需已做 URL 编码。"""
    tpl = proxy.get("raw")
    if tpl is None:
        return None
    if "{owner}" in tpl:
        return tpl.format(owner=owner, repo=repo, branch=branch, path=path)
    if tpl == "":
        return "%s/%s/%s/%s/%s" % (RAW_HOST, owner, repo, branch, path)
    if "raw.githubusercontent.com" in tpl or tpl.endswith("/"):
        return "%s%s/%s/%s/%s" % (tpl, owner, repo, branch, path)
    return tpl


def clone_candidates(github_url):
    """返回 [(说明, 加速后的 URL), ...]，按尝试顺序。"""
    out = []
    for p in GITHUB_PROXIES:
        u = clone_url(github_url, p)
        if u:
            out.append((p["name"], u))
    return out


def raw_candidates(owner, repo, branch, path, only=None):
    """返回 [(说明, 下载 URL), ...]，按尝试顺序。only 可指定单个通道 id。"""
    out = []
    for p in GITHUB_PROXIES:
        if only and p["id"] != only:
            continue
        u = raw_url(owner, repo, branch, path, p)
        if u:
            out.append((p["name"], u))
    return out


def env_hint():
    """给 doctor 用：当前生效的镜像相关环境变量。"""
    keys = ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "PIP_TRUSTED_HOST", "GENSHEN_MIRROR")
    return {k: os.environ.get(k) for k in keys if os.environ.get(k)}
