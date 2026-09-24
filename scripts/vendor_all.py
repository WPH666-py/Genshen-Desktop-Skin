# -*- coding: utf-8 -*-
"""vendor_all.py —— 把 33 个皮肤仓库全部落地到本地。

适合：离线收藏、自建镜像、想一次性拥有全部素材。

    python scripts/vendor_all.py --out D:\\GenshenAll
    python scripts/vendor_all.py --out D:\\GenshenAll --force     # 已存在也重新拉
    python scripts/vendor_all.py --out D:\\GenshenAll --tar       # 顺带打包成 tar.gz

与 `genshen-skin vendor` 的区别：本脚本带 `--tar`、`--jobs`，并且会用当前目录下的
catalog.json（不依赖已安装的包）。
"""
import argparse
import json
import os
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

BAR = "-" * 62


def load_catalog():
    with open(os.path.join(ROOT, "catalog.json"), encoding="utf-8") as f:
        return json.load(f)


def clone(url, dst, force=False, quiet=True):
    """克隆单个仓库，返回 (是否成功, 说明)。"""
    if os.path.isdir(os.path.join(dst, ".git")):
        if not force:
            return True, "已存在"
        r = subprocess.run(["git", "-C", dst, "pull", "--ff-only"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return r.returncode == 0, "已更新" if r.returncode == 0 else "更新失败"
    if os.path.exists(dst) and force:
        import shutil
        shutil.rmtree(dst, ignore_errors=True)
    cmd = ["git", "clone", "--depth", "1", url, dst]
    r = subprocess.run(cmd, stdout=subprocess.PIPE if quiet else None,
                       stderr=subprocess.STDOUT if quiet else None, text=True)
    return r.returncode == 0, "已克隆" if r.returncode == 0 else "克隆失败"


def make_tar(src, out_dir):
    name = os.path.basename(src.rstrip("\\/")) + ".tar.gz"
    path = os.path.join(out_dir, name)
    with tarfile.open(path, "w:gz") as tf:
        tf.add(src, arcname=os.path.basename(src.rstrip("\\/")))
    return path


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f TB" % n


def dir_size(path):
    total = 0
    for base, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(base, f))
            except OSError:
                pass
    return total


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="把 33 个原神皮肤仓库全部克隆到本地")
    ap.add_argument("--out", required=True, help="目标目录")
    ap.add_argument("--force", action="store_true", help="已存在也重新拉取")
    ap.add_argument("--tar", action="store_true", help="每个仓库另外打包成 tar.gz")
    ap.add_argument("--only", default=None, help="只处理逗号分隔的 id 列表")
    args = ap.parse_args(argv)

    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out, exist_ok=True)
    cat = load_catalog()
    skins = cat["skins"]
    if args.only:
        want = {x.strip().lower() for x in args.only.split(",") if x.strip()}
        skins = [s for s in skins if s["id"].lower() in want]
        if not skins:
            print("--only 没匹配到任何 id", file=sys.stderr)
            return 2

    if not any(os.path.exists(os.path.join(p, "git.exe")) or
               subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL) == 0
               for p in [""]):
        print("找不到 git，请先安装：winget install Git.Git / brew install git / apt install git",
              file=sys.stderr)
        return 1

    print("目标目录: %s" % out)
    print("共 %d 套皮肤" % len(skins))
    print(BAR)

    t0 = time.time()
    ok = fail = 0
    failed = []
    for i, s in enumerate(skins, 1):
        dst = os.path.join(out, s["repo"])
        sys.stdout.write("[%2d/%d] %-14s %s ... " % (i, len(skins), s["repo"], s["name"]))
        sys.stdout.flush()
        try:
            good, note = clone(s["url"] + ".git", dst, force=args.force)
        except Exception as e:
            good, note = False, str(e)
        if good:
            size = human(dir_size(dst))
            extra = ""
            if args.tar:
                try:
                    p = make_tar(dst, out)
                    extra = "  +%s" % os.path.basename(p)
                except Exception as e:
                    extra = "  (打包失败: %s)" % e
            print("✓ %s  %s%s" % (note, size, extra))
            ok += 1
        else:
            print("✗ %s" % note)
            failed.append(s["repo"])
            fail += 1

    print(BAR)
    print("完成：成功 %d，失败 %d，用时 %.0f 秒" % (ok, fail, time.time() - t0))
    print("总大小: %s" % human(dir_size(out)))
    if failed:
        print("失败列表: %s" % ", ".join(failed))
        print("可重试: python scripts/vendor_all.py --out \"%s\" --only %s"
              % (out, ",".join(f.replace("Genshen-", "").replace("-Skin", "").lower()
                               for f in failed)))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
