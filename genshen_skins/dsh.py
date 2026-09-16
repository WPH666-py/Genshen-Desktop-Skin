# -*- coding: utf-8 -*-
"""genshen_skins.dsh —— DeepSeek Harness 动态插件（Cordis）载荷准备。

DSH 的皮肤是一个**动态 Cordis 插件**：把皮肤仓库里的 `client.js`
（素材已内嵌为 base64，零配置）喂给 `cordis_define` 的 `code.client`，
再 `cordis_run` 即可。

本模块负责：
  * 把 payload 下载到 `~/.genshen-skins/_dsh/<id>/`（走镜像回退，不怕 raw 被墙）；
  * 校验文件完整（base64 素材没被截断）；
  * 生成一份给 AI 助手照做的 `DEFINE.md`（含 idPrefix、载入步骤、排错）；
  * 可选地把 `host.js` 的 `ASSET_DIR` 改成本机素材目录，以获得全画质原图。

CLI 侧 `genshen-skin dsh <id>` 会把这一切打印出来，AI 直接照做或转述给用户。
"""
import json
import os
import re

from . import repo

DSH_DIR_NAME = "_dsh"


def dsh_home():
    d = os.path.join(repo.home_dir(), DSH_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def work_dir(skin):
    d = os.path.join(dsh_home(), skin["id"])
    os.makedirs(d, exist_ok=True)
    return d


def prefix(skin):
    """cordis_define 的 idPrefix：3–6 位小写英文字母。"""
    pid = re.sub(r"[^a-z]", "", (skin.get("id") or "").lower())
    if len(pid) > 6:
        pid = pid[:6]
    if len(pid) < 3:
        pid = (pid + "skin")[:6]
    return pid


def client_rel(skin):
    paths = skin.get("paths") or {}
    return paths.get("dsh_client")


def host_rel(skin):
    return (skin.get("paths") or {}).get("dsh_host")


def assets_rel(skin):
    return (skin.get("paths") or {}).get("dsh_assets")


def _looks_complete(text):
    """粗查 base64 素材是否完整：出现 data: 标记就有素材，且不应以截断的 base64 结尾。"""
    marks = len(re.findall(r"data:(?:image|audio)/[a-z0-9.+-]+;base64,", text))
    tail = text.rstrip()[-200:]
    truncated = bool(re.search(r"base64,[A-Za-z0-9+/]{0,40}$", tail)) and "==" not in tail
    return marks, truncated


def prepare(skin, quiet=False, with_host=False):
    """下载 DSH payload，返回描述 dict。"""
    rel = client_rel(skin)
    if not rel:
        raise RuntimeError("%s 没有可用的 DSH 客户端文件" % skin["id"])

    work = work_dir(skin)
    client_path = os.path.join(work, "client.js")
    if not quiet:
        print("[genshen] 下载 DSH payload: %s/%s" % (skin["repo"], rel))
    text = repo.fetch_text(skin["repo"], rel)
    with open(client_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    marks, truncated = _looks_complete(text)
    info = {
        "id": skin["id"],
        "idPrefix": prefix(skin),
        "dir": work,
        "client": client_path,
        "client_rel": rel,
        "client_bytes": len(text.encode("utf-8")),
        "asset_marks": marks,
        "truncated": truncated,
        "host": None,
        "assets": None,
        "name": skin.get("name"),
        "char": skin.get("char"),
    }

    if with_host or host_rel(skin):
        hr = host_rel(skin)
        try:
            host_text = repo.fetch_text(skin["repo"], hr)
            # 素材落到本地，再把 ASSET_DIR 指向它，实现全画质原图
            assets_dir = _ensure_dsh_assets(skin, quiet=quiet)
            if assets_dir:
                host_text = re.sub(
                    r'(ASSET_DIR\s*[:=]\s*)([\'"])[^\'"]*\2',
                    lambda m: "%s%s%s%s" % (m.group(1), m.group(2), assets_dir.replace("\\", "\\\\"), m.group(2)),
                    host_text, count=1)
            host_path = os.path.join(work, "host.js")
            with open(host_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(host_text)
            info["host"] = host_path if with_host else None
            info["host_available"] = host_path
            info["assets"] = assets_dir
        except Exception as e:
            info["host_error"] = str(e)

    if not quiet:
        flag = "可能被截断 ⚠" if truncated else "OK"
        print("[genshen] payload %d KB，内嵌素材 %d 处，完整性 %s"
              % (info["client_bytes"] // 1024, marks, flag))
    return info


def _ensure_dsh_assets(skin, quiet=False):
    """把该皮肤 DSH 素材目录拉到本地（供全画质 host.js 使用）。"""
    rel = assets_rel(skin)
    if not rel:
        return None
    local = repo.skin_dir(skin["repo"])
    target = os.path.normpath(os.path.join(local, rel))
    if os.path.isdir(target) and any(os.scandir(target)):
        return target
    # 素材文件清单来自 catalog 的壁纸/语音登记
    wanted = list(skin.get("wallpapers") or []) + list(skin.get("voices") or [])
    if not wanted:
        return None
    for r in wanted:
        dest = os.path.join(local, r)
        if not os.path.exists(dest):
            try:
                repo.download_to(skin["repo"], r, dest, quiet=True)
            except Exception:
                pass
    return target if os.path.isdir(target) else None


def define_md(skin, info):
    """生成给 AI 助手照做的操作单。"""
    p = info["idPrefix"]
    lines = [
        "# DSH 动态插件载荷 · %s" % skin["name"],
        "",
        "已在本地准备好，**不要再重新下载**：",
        "",
        "- 客户端源码：`%s`（%d KB，素材已内嵌 base64，零配置）"
        % (info["client"], info["client_bytes"] // 1024),
        "- 建议 `idPrefix`：`%s`" % p,
    ]
    if info.get("host_available"):
        lines.append("- 可选 Host（全画质原图）：`%s`" % info["host_available"])
        if info.get("assets"):
            lines.append("- 素材目录（host.js 的 ASSET_DIR 已指向它）：`%s`" % info["assets"])
    lines += [
        "",
        "## 步骤",
        "",
        "1. 读取上面的客户端源码文件全文（完整读取，不要节选、不要改动 base64 串）。",
        "2. 调用 `cordis_define`：",
        "   - `plugin.kind = \"new\"`，`idPrefix = \"%s\"`" % p,
        "   - `name = \"%s动态皮肤\"`" % skin["char"],
        "   - `purpose = \"原神%s动态皮肤：点击播放元素爆发语音与特效，可切换壁纸\"" % skin["char"],
        "   - `code.client` = 源码全文",
        "3. 调用 `cordis_run`（mode `run`）；若返回 awaiting-approval，提示用户在卡片上允许。",
        "4. 告知用户：页面右下角出现%s皮肤；点击释放元素爆发（中文语音 + 特效），"
        "右键菜单含「切换壁纸」「一键卸载」。" % skin["char"],
        "",
        "## 排错",
        "",
        "- `cordis_define` 报语法错误 → 多半是文件被截断，重新完整读取整个文件。",
        "- 插件是**进程内动态插件**，DSH 重启后需重新 define + run。",
        "- 卸载：右键菜单「一键卸载」，或 `cordis_undefine %s`。" % p,
        "",
        "## 素材版权",
        "",
        "立绘、壁纸与语音归米哈游（miHoYo/HoYoverse），仅供个人学习娱乐。",
    ]
    if info.get("truncated"):
        lines += ["", "> ⚠ 本地文件结尾疑似被截断，请核对文件大小 %d 字节。" % info["client_bytes"]]
    return "\n".join(lines) + "\n"


def write_define_md(skin, info):
    path = os.path.join(info["dir"], "DEFINE.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(define_md(skin, info))
    return path


def emit(skin, quiet=False, with_host=False, as_json=False):
    """准备载荷并写 DEFINE.md；返回 info。"""
    info = prepare(skin, quiet=quiet, with_host=with_host)
    info["define_md"] = write_define_md(skin, info)
    if as_json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    elif not quiet:
        print()
        print(define_md(skin, info))
    return info
