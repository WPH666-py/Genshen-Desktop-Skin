# -*- coding: utf-8 -*-
"""CLI 与核心模块的离线测试。

只跑**无副作用、不联网**的路径：列表、查询、目录、镜像信息、参数解析、
壁纸模式解析、镜像 URL 拼装等。
有副作用的命令（install / pet / wallpaper / ide / uninstall）不在这里跑，
它们在真实机器上单独验证（见 docs/INSTALL.md）。

    python -m unittest discover -s tests -v
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genshen_skins import cli, mirror, repo, targets, wallpaper   # noqa: E402


def run_cli(*argv):
    """在进程内跑一次 CLI，返回 (退出码, stdout 文本)。"""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(list(argv))
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 1
    return rc, out.getvalue() + err.getvalue()


class TempHomeMixin(unittest.TestCase):
    """把 GENSHEN_HOME 指到临时目录，保证测试不碰用户真实目录。"""

    def setUp(self):
        self._old = os.environ.get("GENSHEN_HOME")
        self._tmp = tempfile.mkdtemp(prefix="genshen-test-")
        os.environ["GENSHEN_HOME"] = self._tmp

    def tearDown(self):
        if self._old is None:
            os.environ.pop("GENSHEN_HOME", None)
        else:
            os.environ["GENSHEN_HOME"] = self._old
        repo.rmtree(self._tmp)


class TestCliOffline(TempHomeMixin):
    def test_list(self):
        rc, out = run_cli("list")
        self.assertEqual(rc, 0)
        self.assertIn("共 29 套", out)
        self.assertIn("skirk", out)
        self.assertIn("clorinde", out)

    def test_version(self):
        rc, out = run_cli("--version")
        self.assertIn("genshen-desktop-skin", out)

    def test_show_by_id(self):
        rc, out = run_cli("show", "furina")
        self.assertEqual(rc, 0)
        self.assertIn("芙宁娜", out)
        self.assertIn("Genshen-Furina-Skin", out)
        self.assertIn("genshen-skin install furina", out)

    def test_show_chinese(self):
        rc, out = run_cli("show", "丝柯克")
        self.assertEqual(rc, 0)
        self.assertIn("霜刃渊海", out)

    def test_show_unknown_exits_2(self):
        rc, out = run_cli("show", "不存在的角色xyz")
        self.assertEqual(rc, 2)
        self.assertIn("没找到", out)

    def test_show_unknown_suggests_candidates(self):
        rc, out = run_cli("show", "雷电")
        self.assertEqual(rc, 0)          # "雷电" 能命中 雷电将军
        self.assertIn("雷电将军", out)

    def test_catalog_json(self):
        rc, out = run_cli("catalog", "--json")
        self.assertEqual(rc, 0)
        data = json.loads(out[out.index("{"):])
        self.assertEqual(len(data["skins"]), 29)

    def test_catalog_md(self):
        rc, out = run_cli("catalog", "--md")
        self.assertEqual(rc, 0)
        self.assertIn("| # | ID | 皮肤 |", out)
        self.assertEqual(out.count("| [Genshen-"), 29)

    def test_paths(self):
        rc, out = run_cli("paths")
        self.assertEqual(rc, 0)
        self.assertIn(self._tmp, out)

    def test_mirror_lists_both_chinese_mirrors(self):
        rc, out = run_cli("mirror")
        self.assertEqual(rc, 0)
        self.assertIn("pypi.tuna.tsinghua.edu.cn", out)
        self.assertIn("mirrors.ustc.edu.cn", out)
        self.assertIn("只读镜像", out)

    def test_mirror_set(self):
        rc, out = run_cli("mirror", "--set", "ustc")
        self.assertEqual(rc, 0)
        self.assertIn("中国科学技术大学", out)

    def test_mirror_set_invalid(self):
        rc, out = run_cli("mirror", "--set", "nope")
        self.assertEqual(rc, 2)

    def test_requires_subcommand(self):
        with self.assertRaises(SystemExit):
            cli.main([])

    def test_env_runs(self):
        rc, out = run_cli("env")
        self.assertEqual(rc, 0)
        self.assertIn("原神皮肤集合", out)


class TestWallpaperModes(unittest.TestCase):
    def setUp(self):
        from genshen_skins import catalog as c
        self.skin = c.find_skin(c.load_catalog(), "furina")

    def test_numeric_modes(self):
        idx, label = wallpaper.pick_mode(self.skin, "1")
        self.assertEqual(idx, 0)
        self.assertIn("第 1 张", label)
        idx, _ = wallpaper.pick_mode(self.skin, "3")
        self.assertEqual(idx, 2)

    def test_random_in_range(self):
        n = len(self.skin["wallpapers"])
        for _ in range(30):
            idx, _ = wallpaper.pick_mode(self.skin, "random")
            self.assertTrue(0 <= idx < n)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            wallpaper.pick_mode(self.skin, "99")

    def test_zero_is_invalid(self):
        with self.assertRaises(ValueError):
            wallpaper.pick_mode(self.skin, "0")

    def test_garbage_is_invalid(self):
        with self.assertRaises(ValueError):
            wallpaper.pick_mode(self.skin, "abc")

    def test_parse_size(self):
        self.assertEqual(wallpaper.parse_size("1920x1080"), (1920, 1080))
        self.assertEqual(wallpaper.parse_size("2560×1440"), (2560, 1440))
        self.assertIsNone(wallpaper.parse_size(None))
        with self.assertRaises(ValueError):
            wallpaper.parse_size("big")

    def test_screen_size_sane(self):
        w, h = wallpaper.screen_size()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)


class TestMirrorHelpers(unittest.TestCase):
    def test_pip_args_official_empty(self):
        self.assertEqual(mirror.pip_install_args("official"), [])

    def test_pip_args_mirror(self):
        args = mirror.pip_install_args("tuna")
        self.assertIn("-i", args)
        self.assertIn("https://pypi.tuna.tsinghua.edu.cn/simple", args)
        self.assertIn("--trusted-host", args)

    def test_both_chinese_mirrors_present(self):
        self.assertIn("tuna", mirror.PIP_MIRRORS)
        self.assertIn("ustc", mirror.PIP_MIRRORS)
        self.assertEqual(mirror.PIP_MIRRORS["ustc"]["index"],
                         "https://mirrors.ustc.edu.cn/pypi/simple")

    def test_clone_candidates_include_direct_first(self):
        cands = mirror.clone_candidates("https://github.com/o/r.git")
        self.assertTrue(cands)
        self.assertEqual(cands[0][1], "https://github.com/o/r.git", "直连应排第一")
        urls = [u for _l, u in cands]
        self.assertTrue(any("ghfast" in u for u in urls))
        self.assertNotIn(None, urls, "clone 候选里不应出现 None")

    def test_raw_candidates_all_usable(self):
        cands = mirror.raw_candidates("WPH666-py", "Genshen-Skirk-Skin", "main", "skin.json")
        self.assertTrue(cands)
        for label, url in cands:
            self.assertTrue(url.startswith("http"), "%s 生成的 URL 非法: %r" % (label, url))
            self.assertIn("skin.json", url)

    def test_raw_jsdelivr_shape(self):
        cands = dict(mirror.raw_candidates("o", "r", "main", "a/b.js"))
        self.assertEqual(cands["jsDelivr CDN"], "https://cdn.jsdelivr.net/gh/o/r@main/a/b.js")

    def test_raw_candidates_filter(self):
        cands = mirror.raw_candidates("o", "r", "main", "x", only="direct")
        self.assertEqual(len(cands), 1)


class TestRepoHelpers(TempHomeMixin):
    def test_home_dir_respects_env(self):
        self.assertEqual(repo.home_dir(), os.path.abspath(self._tmp))

    def test_skin_dir(self):
        self.assertEqual(repo.skin_dir("Genshen-X-Skin"),
                         os.path.join(os.path.abspath(self._tmp), "Genshen-X-Skin"))

    def test_rmtree_handles_readonly(self):
        """Windows 上 git 的 pack 文件是只读的，rmtree 必须能删掉。"""
        import stat
        d = os.path.join(self._tmp, "sub")
        os.makedirs(os.path.join(d, "objects"))
        f = os.path.join(d, "objects", "pack.pack")
        with open(f, "wb") as fh:
            fh.write(b"x")
        os.chmod(f, stat.S_IREAD)
        try:
            self.assertTrue(repo.rmtree(d))
            self.assertFalse(os.path.exists(d))
        finally:
            try:
                os.chmod(f, stat.S_IWRITE)
            except OSError:
                pass

    def test_rmtree_missing_path_is_ok(self):
        self.assertTrue(repo.rmtree(os.path.join(self._tmp, "nope")))
        self.assertTrue(repo.rmtree(""))

    def test_is_cloned_false_for_empty_dir(self):
        d = os.path.join(self._tmp, "Genshen-Y-Skin")
        os.makedirs(d)
        self.assertFalse(repo.is_cloned(d))


class TestTargetsOffline(TempHomeMixin):
    def test_detect_editors_returns_list(self):
        eds = targets.detect_editors()
        self.assertIsInstance(eds, list)
        for ed in eds:
            self.assertIn("id", ed)
            self.assertIn("name", ed)
            self.assertIn("extdir", ed)

    def test_find_editor_unknown(self):
        self.assertIsNone(targets.find_editor("这个编辑器不存在"))

    def test_detect_jetbrains_returns_list(self):
        self.assertIsInstance(targets.detect_jetbrains(), list)

    def test_vsix_extension_id_on_bad_file(self):
        p = os.path.join(self._tmp, "bad.vsix")
        with open(p, "wb") as f:
            f.write(b"not a zip")
        self.assertIsNone(targets.vsix_extension_id(p))

    def test_vsix_extension_id_missing_file(self):
        self.assertIsNone(targets.vsix_extension_id(os.path.join(self._tmp, "nope.vsix")))

    def test_detect_dsh_returns_tuple(self):
        dsh, note = targets.detect_dsh()
        self.assertIsInstance(dsh, bool)
        self.assertIsInstance(note, str)

    def test_describe_env_shape(self):
        info = targets.describe_env()
        for k in ("platform", "python", "screen", "pillow", "proxy", "dsh", "editors"):
            self.assertIn(k, info)
        self.assertEqual(len(info["screen"]), 2)


class TestCatalogLookupModule(TempHomeMixin):
    def test_visible_targets(self):
        from genshen_skins import catalog as c
        sk = c.find_skin(c.load_catalog(), "furina")
        vis = c.visible(sk)
        self.assertIn("dsh", vis)
        self.assertIn("desktop", vis)

    def test_search_ranks(self):
        from genshen_skins import catalog as c
        cat = c.load_catalog()
        hits = c.search(cat, "水")
        self.assertTrue(hits, "按元素'水'应有结果")

    def test_catalog_path_exists(self):
        from genshen_skins import catalog as c
        self.assertTrue(os.path.exists(c.catalog_path()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
