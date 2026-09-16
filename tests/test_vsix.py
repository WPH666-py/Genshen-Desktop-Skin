# -*- coding: utf-8 -*-
"""VSIX 安装 / 卸载测试（合成 VSIX，不联网、不碰真编辑器）。

真实皮肤仓库里的 .vsix 是编辑器扩展包，其"没有 CLI 时解压到扩展目录"这条回退路径
（Trae / CodeX 用户走的就是它）风险最高，因此这里用合成的 VSIX 把整条链路测到：
读扩展 ID → 解压安装 → 覆盖安装 → 卸载 → 坏文件处理。
"""
import json
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genshen_skins import repo, targets   # noqa: E402

PKG = {
    "name": "genshen-fake-skin",
    "publisher": "wp666",
    "version": "1.0.0",
    "displayName": "假皮肤（测试用）",
    "main": "./extension.js",
    "engines": {"vscode": "^1.60.0"},
    "contributes": {
        "commands": [
            {"command": "fakeSkin.show", "title": "假皮肤：显示"},
            {"command": "fakeSkin.uninstall", "title": "假皮肤：卸载"},
        ]
    },
}
EXT_ID = "wp666.genshen-fake-skin"


def make_vsix(path, pkg=None):
    """造一个结构正确的 .vsix（就是个 zip，内含 extension/ 目录）。"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("extension/package.json", json.dumps(pkg or PKG, ensure_ascii=False))
        z.writestr("extension/extension.js", "// fake\n")
        z.writestr("extension/icon.png", b"\x89PNG\r\n\x1a\n")
        z.writestr("[Content_Types].xml", "<Types/>")
    return path


class TestVsixHelpers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="genshen-vsix-")

    def tearDown(self):
        repo.rmtree(self.tmp)

    def test_reads_extension_id(self):
        p = make_vsix(os.path.join(self.tmp, "a.vsix"))
        self.assertEqual(targets.vsix_extension_id(p), EXT_ID)

    def test_id_is_none_for_non_zip(self):
        p = os.path.join(self.tmp, "bad.vsix")
        with open(p, "wb") as f:
            f.write(b"definitely not a zip")
        self.assertIsNone(targets.vsix_extension_id(p))

    def test_id_is_none_for_zip_without_package_json(self):
        p = os.path.join(self.tmp, "nopkg.vsix")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("extension/readme.md", "hi")
        self.assertIsNone(targets.vsix_extension_id(p))

    def test_id_is_none_for_missing_file(self):
        self.assertIsNone(targets.vsix_extension_id(os.path.join(self.tmp, "nope.vsix")))


class TestVsixInstallFallback(unittest.TestCase):
    """编辑器没有 CLI 时的解压安装路径。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="genshen-vsix-")
        self.extdir = os.path.join(self.tmp, "extensions")
        os.makedirs(self.extdir)
        self.vsix = make_vsix(os.path.join(self.tmp, "fake.vsix"))
        self.editor = {"id": "fake", "name": "FakeTrae", "cli": None, "extdir": self.extdir}
        self.target = os.path.join(self.extdir, EXT_ID)

    def tearDown(self):
        repo.rmtree(self.tmp)

    def test_install_extracts_into_extension_dir(self):
        ok, note = targets.install_vsix(self.editor, self.vsix, quiet=True)
        self.assertTrue(ok, note)
        self.assertTrue(os.path.isdir(self.target))
        for name in ("package.json", "extension.js", "icon.png"):
            self.assertTrue(os.path.exists(os.path.join(self.target, name)),
                            "解压后缺少 %s" % name)

    def test_installed_package_json_is_intact(self):
        targets.install_vsix(self.editor, self.vsix, quiet=True)
        with open(os.path.join(self.target, "package.json"), encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual("%s.%s" % (meta["publisher"], meta["name"]), EXT_ID)
        self.assertEqual(meta["displayName"], PKG["displayName"])

    def test_reinstall_overwrites_without_leftovers(self):
        targets.install_vsix(self.editor, self.vsix, quiet=True)
        stale = os.path.join(self.target, "STALE.txt")
        with open(stale, "w") as f:
            f.write("should be gone")
        ok, _ = targets.install_vsix(self.editor, self.vsix, quiet=True)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(stale), "覆盖安装残留了旧文件")

    def test_uninstall_removes_extension(self):
        targets.install_vsix(self.editor, self.vsix, quiet=True)
        ok, _ = targets.uninstall_vsix(self.editor, EXT_ID, quiet=True)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(self.target))

    def test_bad_vsix_is_rejected(self):
        p = os.path.join(self.tmp, "bad.vsix")
        with open(p, "wb") as f:
            f.write(b"not a zip")
        ok, note = targets.install_vsix(self.editor, p, quiet=True)
        self.assertFalse(ok)
        self.assertIn("扩展 ID", note)

    def test_missing_vsix_is_rejected(self):
        ok, note = targets.install_vsix(self.editor, os.path.join(self.tmp, "x.vsix"), quiet=True)
        self.assertFalse(ok)
        self.assertIn("找不到", note)

    def test_install_without_extdir_fails_cleanly(self):
        ok, note = targets.install_vsix({"name": "X", "cli": None, "extdir": None},
                                        self.vsix, quiet=True)
        self.assertFalse(ok)
        self.assertIn("扩展目录", note)


class TestCatalogVsixPaths(unittest.TestCase):
    """catalog 里登记的 vsix 路径形状必须对 —— 这是客户端据此拼 URL 的依据。"""

    def test_vsix_paths_point_into_vscode_extension_dir(self):
        from genshen_skins import catalog as c
        for s in c.load_catalog()["skins"]:
            v = s["paths"]["vsix"]
            if not v:
                continue
            self.assertTrue(v.startswith("vscode-extension/"),
                            "%s 的 vsix 不在 vscode-extension/ 下: %r" % (s["id"], v))
            self.assertTrue(v.endswith(".vsix"), "%s 的 vsix 后缀不对: %r" % (s["id"], v))

    def test_extension_ids_look_like_publisher_name(self):
        import re
        from genshen_skins import catalog as c
        for s in c.load_catalog()["skins"]:
            ext = s.get("ext")
            if not ext:
                continue
            self.assertRegex(ext["id"], r"^[a-z0-9][a-z0-9-]*\.[a-z0-9][a-z0-9-]*$",
                             "%s 的扩展 ID 形状可疑: %r" % (s["id"], ext["id"]))
            self.assertTrue(ext["id"].startswith("wp666."),
                            "%s 的扩展 ID 发布者不是 wp666: %r" % (s["id"], ext["id"]))
            self.assertRegex(ext["id"], r"genshen-[a-z]+-skin$",
                             "%s 的扩展 ID 命名不符: %r" % (s["id"], ext["id"]))

    def test_show_command_matches_id(self):
        from genshen_skins import catalog as c
        for s in c.load_catalog()["skins"]:
            ext = s.get("ext")
            if not ext:
                continue
            self.assertTrue(ext["show"], "%s 没有 show 命令" % s["id"])
            self.assertTrue(ext["show"].endswith(".show"), ext["show"])
            self.assertTrue(ext["uninstall"].endswith(".uninstall"), ext["uninstall"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
