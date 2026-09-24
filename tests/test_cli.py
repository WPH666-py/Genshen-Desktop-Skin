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
        self.assertIn("共 33 套", out)
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
        self.assertEqual(len(data["skins"]), 33)

    def test_catalog_md(self):
        rc, out = run_cli("catalog", "--md")
        self.assertEqual(rc, 0)
        self.assertIn("| # | ID | 皮肤 |", out)
        self.assertEqual(out.count("| [Genshen-"), 33)

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

    def test_no_args_shows_all_commands(self):
        """直接敲 `genshen-skin` 应打印全部命令总览，而不是参数错误。

        这是「装完包之后用户想看到什么」——不该甩一个
        "the following arguments are required: cmd"。
        """
        rc, out = run_cli()
        self.assertEqual(rc, 0, "不带参数应当正常退出并给出帮助")
        self.assertIn("全部命令总览", out)
        # 每个子命令都要在总览里出现
        for name in ("list", "show", "install", "uninstall", "wallpaper", "export",
                     "pet", "ide", "dsh", "deepking", "sync", "vendor", "mirror",
                     "env", "doctor", "catalog", "paths", "commands"):
            self.assertIn(name, out, "命令总览里漏了 %s" % name)

    def test_commands_subcommand_and_aliases(self):
        for name in ("commands", "help", "?"):
            rc, out = run_cli(name)
            self.assertEqual(rc, 0, "`%s` 应返回 0" % name)
            self.assertIn("全部命令总览", out, "`%s` 没有输出总览" % name)

    def test_commands_help_mentions_key_flags(self):
        rc, out = run_cli("commands")
        for flag in ("--mode", "--fit", "--editor", "--keep-files",
                     "--autostart", "--with-host", "--set", "--out"):
            self.assertIn(flag, out, "命令总览里没提 %s" % flag)

    def test_commands_help_mentions_all_five_forms(self):
        rc, out = run_cli("commands")
        for form in ("genshen-skin list", "gss list", "python -m genshen-skin list",
                     "python -m genshen_skin list", "python -m genshen_skins list"):
            self.assertIn(form, out, "命令总览里没写等价写法 %r" % form)

    def test_commands_help_mentions_chinese_aliases(self):
        rc, out = run_cli("commands")
        for alias in ("水神", "草神", "雷神"):
            self.assertIn(alias, out, "命令总览里没提中文别名 %s" % alias)

    def test_unknown_command_still_errors(self):
        """拼错的命令仍应报错，不能被总览吞掉。"""
        with self.assertRaises(SystemExit):
            cli.main(["nonexistent-cmd"])

    def test_help_flag_still_works(self):
        with self.assertRaises(SystemExit):
            cli.main(["--help"])

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


class TestInvocationNames(unittest.TestCase):
    """调用方式有五种，全部等价，都要能用。

    真实踩坑记录：用户装完后敲 `genshen-skin` 报"找不到命令"（pip 的 Scripts 目录
    不在 PATH），接着试 `python -m genshen-skin`。

    这里有个反直觉的事实（踩过一次，记下来别再搞错）：
    **`python -m genshen-skin` 是可行的**，因为 `python -m` 是按**字符串**在
    sys.path 里找模块，不要求名字是合法标识符；只有 `import genshen-skin` 这种
    语句形式才会 SyntaxError。所以包里额外放了 `genshen-skin.py` 顶层入口。

    五种等价写法：
        genshen-skin list                控制台命令
        gss list                         控制台命令别名
        python -m genshen-skin list      顶层 shim（连字符）
        python -m genshen_skin list      顶层 shim（下划线单数）
        python -m genshen_skins list     正式包（下划线复数）
    """

    def test_real_package_importable(self):
        import importlib
        m = importlib.import_module("genshen_skins")
        self.assertTrue(hasattr(m, "__version__"))

    def test_package_has_main(self):
        """`python -m genshen_skins` 要能用。"""
        import importlib
        m = importlib.import_module("genshen_skins.__main__")
        self.assertTrue(hasattr(m, "main"), "genshen_skins/__main__.py 必须暴露 main")

    def test_dashed_shim_is_findable_by_importlib(self):
        """带连字符的模块名对 importlib 是合法的（字符串查找，不走语法解析）。"""
        import importlib.machinery
        import importlib.util
        base = os.path.join(ROOT, "genshen-skin.py")
        self.assertTrue(os.path.exists(base), "缺少 genshen-skin.py 顶层入口")
        spec = importlib.machinery.PathFinder.find_spec("genshen-skin", [ROOT])
        self.assertIsNotNone(spec, "genshen-skin.py 无法被找到")
        self.assertTrue(spec.origin.endswith("genshen-skin.py"))

    def test_import_statement_with_hyphen_is_syntax_error(self):
        """但 `import genshen-skin` 一定是语法错误 —— 这两种形式别混。"""
        with self.assertRaises(SyntaxError):
            compile("import genshen-skin", "<test>", "exec")

    def test_both_shims_exist_and_delegate(self):
        for name in ("genshen-skin.py", "genshen_skin.py"):
            p = os.path.join(ROOT, name)
            self.assertTrue(os.path.exists(p), "缺少顶层入口 %s" % name)
            with open(p, encoding="utf-8") as f:
                src = f.read()
            self.assertIn("from genshen_skins.cli import main", src,
                          "%s 应转发到 genshen_skins.cli.main" % name)
            self.assertIn('__name__ == "__main__"', src,
                          "%s 需要 __main__ 守卫，否则 -m 跑不起来" % name)

    def test_shims_are_declared_as_py_modules(self):
        """顶层 shim 必须被 setuptools 打进 wheel，否则装完还是 ModuleNotFoundError。"""
        with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as f:
            toml_text = f.read()
        self.assertIn("py-modules", toml_text, "pyproject 缺 py-modules 声明")
        for name in ("genshen-skin", "genshen_skin"):
            self.assertIn('"%s"' % name, toml_text,
                          "pyproject 的 py-modules 里没有 %s" % name)
        with open(os.path.join(ROOT, "setup.py"), encoding="utf-8") as f:
            setup_text = f.read()
        self.assertIn("py_modules", setup_text, "setup.py 缺 py_modules 声明")
        with open(os.path.join(ROOT, "MANIFEST.in"), encoding="utf-8") as f:
            manifest = f.read()
        for name in ("genshen-skin.py", "genshen_skin.py"):
            self.assertIn(name, manifest, "MANIFEST.in 里没有 %s" % name)

    def test_console_scripts_are_declared(self):
        with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn('genshen-skin = "genshen_skins.cli:main"', text,
                      "pyproject 里 genshen-skin 入口点被改了")
        self.assertIn('gss = "genshen_skins.cli:main"', text,
                      "pyproject 里 gss 别名入口点被改了")

    def test_setup_py_matches_pyproject_entry_points(self):
        with open(os.path.join(ROOT, "setup.py"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("genshen-skin = genshen_skins.cli:main", text)
        self.assertIn("gss = genshen_skins.cli:main", text)

    # 曾经因为想当然，把「python -m genshen-skin 必然失败」这个错误结论写进了三份文档。
    # README 与 docs/INSTALL.md 已整段更正，不允许再出现这些字眼；
    # AGENTS.md 因为版本守卫不允许改写既有行，只能在原文后面追加「以上两行作废」的更正，
    # 所以对它放宽为：错误说法**可以**留痕，但必须在附近明确标出作废。
    WRONG_CLAIMS = ("No module named genshen-skin",
                    "模块名不能含连字符",
                    "不要写成 `python -m genshen-skin`")
    RETRACTION_MARKS = ("作废", "曾写错", "那是错的", "已更正", "有误")

    def _docs_with_wrong_claim(self, rel):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as f:
            text = f.read()
        return [bad for bad in self.WRONG_CLAIMS if bad in text]

    def test_readme_and_install_do_not_claim_dashed_form_impossible(self):
        """这两份文档不允许出现错误结论 —— 它们可以整段改写。"""
        for rel in ("README.md", "docs/INSTALL.md"):
            self.assertEqual(self._docs_with_wrong_claim(rel), [],
                             "%s 里还留着错误结论" % rel)

    def test_agents_md_wrong_claim_is_retracted(self):
        """AGENTS.md 里若留着旧说法，必须紧跟明确的作废标记。

        版本守卫不允许改写既有行（会判为"疑似覆盖"），所以只能追加更正 ——
        这条测试保证更正不会被误删，也就不会有"没有更正的错误说法"被 AI 读到。
        """
        p = os.path.join(ROOT, "AGENTS.md")
        if not os.path.exists(p):
            self.skipTest("没有 AGENTS.md")
        with open(p, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            if not any(bad in line for bad in self.WRONG_CLAIMS):
                continue
            window = lines[i:i + 25]          # 允许更正出现在紧随其后的若干行
            self.assertTrue(
                any(m in w for m in self.RETRACTION_MARKS for w in window),
                "AGENTS.md 第 %d 行有错误说法却没有作废标记：%s" % (i + 1, line.strip()))

    def test_agents_md_documents_the_single_invocation_form(self):
        """文档只推一种调用写法：Windows `py -3 -m genshen_skins`，其他平台 `python3 -m`。

        旧契约是「五种等价写法都要在 AGENTS.md 里写明」，现已作废 ——
        罗列多种写法只让用户挑花眼，而且每一种都得配一段 PATH 排错。
        现在统一成 py -3 -m：不依赖 Scripts 在不在 PATH，也就没有那类报错。
        """
        with open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("py -3 -m genshen_skins", text, "AGENTS.md 没写统一调用写法")
        self.assertIn("python3 -m", text, "AGENTS.md 没写 macOS / Linux 的等价写法")
        self.assertNotIn("五种写法", text, "AGENTS.md 还在宣传『五种等价写法』")
        self.assertNotIn("gss list", text, "AGENTS.md 还在宣传 gss 短别名")

    def test_docs_document_the_path_fallback(self):
        """PATH 踩坑的说明必须留在文档里 —— 用户就是这么被绊住的。"""
        for rel in ("README.md", "docs/INSTALL.md"):
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("genshen_skins", text, "%s 没写模块名" % rel)
            self.assertIn("PATH", text, "%s 没写 PATH 排查" % rel)
            self.assertIn("Scripts", text, "%s 没写 Scripts 目录" % rel)

    def test_docs_document_the_path_fallback(self):
        """PATH 踩坑的说明必须留在文档里 —— 用户就是这么被绊住的。"""
        for rel in ("README.md", "docs/INSTALL.md"):
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("genshen_skins", text, "%s 没写正确的模块名" % rel)
            self.assertIn("PATH", text, "%s 没写 PATH 排查" % rel)
            self.assertIn("Scripts", text, "%s 没写 Scripts 目录" % rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
