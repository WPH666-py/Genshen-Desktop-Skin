# -*- coding: utf-8 -*-
"""genshen_skins.proxy —— 自动探测本机代理，并把它交给 git / pip 子进程。

为什么需要：
    * git 读 **Windows 系统代理**（注册表 Internet Settings），所以桌面代理软件一开
      （Clash / verge / v2ray …）git 就能用，`genshen-skin install` 看着像"没问题"；
    * pip 与 Python 的 urllib/requests **故意不读注册表**，只看 HTTP_PROXY /
      HTTPS_PROXY 环境变量。桌面代理软件默认通常不写这两个变量 —— 于是 pip 直连
      pypi.org，在受限网络下就报 SSL UNEXPECTED_EOF / Read timed out。
    本模块把"探测到的代理"显式喂给这两条通道，用户不必自己配环境变量。

探测顺序：
    1. GENSHEN_PROXY 显式指定；
    2. 环境变量 HTTP_PROXY / HTTPS_PROXY / ALL_PROXY（含小写形式）—— 尊重用户设置；
    3. Windows 注册表 Internet Settings 的 ProxyServer（系统代理）；
    4. 本机常见代理端口探测（127.0.0.1:7897/7890/10809/…）。

关闭方式：设 GENSHEN_NO_PROXY=1；显式指定：GENSHEN_PROXY=http://host:port。
"""
import os
import socket
import subprocess
import sys

# 常见桌面代理软件默认监听端口
COMMON_PORTS = (7897, 7890, 7891, 10809, 10808, 1080, 8888, 2080, 20171, 33210)
PROBE_TIMEOUT = 0.35

ENV_KEYS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

_cached = None
_cached_source = None
_detected = False


def _flag(name):
    v = os.environ.get(name, "").strip().lower()
    return v not in ("", "0", "false", "no", "off")


def _disabled():
    return _flag("GENSHEN_NO_PROXY") or _flag("DEEPSKINS_NO_PROXY")


def _normalize(value):
    """统一成 http://host:port 形式；兼容 localhost:7897 / 127.0.0.1:7897。"""
    if not value:
        return None
    v = value.strip().strip('"').strip("'")
    if not v:
        return None
    if "://" not in v:
        v = "http://" + v
    return v.rstrip("/")


def _from_override():
    for key in ("GENSHEN_PROXY", "DEEPSKINS_PROXY"):
        v = os.environ.get(key)
        if v:
            return _normalize(v), key
    return None, None


def _from_env():
    for k in ENV_KEYS:
        v = os.environ.get(k)
        if v:
            return _normalize(v), "环境变量 %s" % k
    return None, None


def _from_windows_registry():
    """读 Windows 系统代理（HKCU Internet Settings），仅在 ProxyEnable=1 时生效。"""
    if sys.platform != "win32":
        return None, None
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        try:
            enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
        finally:
            winreg.CloseKey(key)
        if not enable or not server:
            return None, None
        server = str(server)
        # 形如 "host:port" 或 "http=host:port;https=host:port"
        if "=" in server:
            parts = dict(p.split("=", 1) for p in server.split(";") if "=" in p)
            server = parts.get("https") or parts.get("http") or ""
        url = _normalize(server)
        return (url, "Windows 系统代理(注册表)") if url else (None, None)
    except Exception:
        return None, None


def _port_open(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT):
            return True
    except OSError:
        return False


def _from_local_ports():
    for port in COMMON_PORTS:
        if _port_open(port):
            return "http://127.0.0.1:%d" % port, "本机端口探测(%d 在监听)" % port
    return None, None


def detect(force=False):
    """返回 (proxy_url 或 None, 来源说明 或 None)。结果会缓存。"""
    global _cached, _cached_source, _detected
    if _detected and not force:
        return _cached, _cached_source
    if _disabled():
        _cached, _cached_source, _detected = None, "已由 GENSHEN_NO_PROXY 关闭", True
        return _cached, _cached_source

    for finder in (_from_override, _from_env, _from_windows_registry, _from_local_ports):
        url, source = finder()
        if url:
            _cached, _cached_source, _detected = url, source, True
            return _cached, _cached_source

    _cached, _cached_source, _detected = None, "未探测到代理", True
    return _cached, _cached_source


def env_with_proxy(base=None):
    """返回一份带代理环境变量的副本，供 pip 等"只认环境变量"的程序使用。"""
    env = dict(base if base is not None else os.environ)
    url, _ = detect()
    if url:
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            env[k] = url
    return env


def pip_args():
    """给 pip 命令追加的参数（pip 自己也会读环境变量，这里再显式传一次更稳）。"""
    url, _ = detect()
    return ["--proxy", url] if url else []


def git_config_args():
    """给 git 命令追加的 -c 参数。

    只有"探测到代理、且用户 git 全局没配代理"时才注入 —— 免得覆盖用户自己的配置。
    """
    url, _ = detect()
    if not url:
        return []
    try:
        configured = subprocess.run(
            ["git", "config", "--global", "--get", "http.proxy"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, text=True).stdout.strip()
    except Exception:
        configured = ""
    if configured:
        return []
    return ["-c", "http.proxy=%s" % url, "-c", "https.proxy=%s" % url]


def opener():
    """返回一个走探测代理的 urllib opener（给下载 raw 文件用）。"""
    import urllib.request
    url, _ = detect()
    if not url:
        return urllib.request.build_opener()
    handler = urllib.request.ProxyHandler({"http": url, "https": url})
    return urllib.request.build_opener(handler)


def describe():
    url, source = detect(force=True)
    if url:
        return "代理: %s  (来源: %s)" % (url, source)
    return "代理: 未探测到  (%s)" % (source or "无")
