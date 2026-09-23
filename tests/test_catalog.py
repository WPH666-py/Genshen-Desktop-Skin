# -*- coding: utf-8 -*-
"""catalog.json 完整性测试。

catalog.json 是整个集合的事实来源，AI 助手、CLI、README 都从它读数据。
它由 `scripts/sync_catalog.py` 从 31 个皮肤仓库实测生成，所以这里重点检查
"生成结果是否自洽"：字段齐不齐、路径指向的文件在不在、能力标记有没有矛盾。

    python -m unittest discover -s tests -v
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genshen_skins import catalog as cat_mod      # noqa: E402
from genshen_skins import dsh                     # noqa: E402

REQUIRED_SKIN_FIELDS = ("id", "no", "repo", "url", "raw", "clone", "char", "charEn",
                        "aliases", "name", "accent", "caps", "paths", "wallpapers", "voices")
REQUIRED_PATH_KEYS = ("dsh_client", "dsh_host", "vsix", "desktop_ps1", "desktop_bat",
                      "deepking_css", "skin_json")
REQUIRED_CAPS = ("dsh", "desktop", "vscode", "deepking")

EXPECTED_COUNT = 31
OWNER = "WPH666-py"


class TestCatalogStructure(unittest.TestCase):
    def setUp(self):
        self.cat = cat_mod.load_catalog(refresh=True)
        self.skins = self.cat["skins"]

    def test_count(self):
        self.assertEqual(self.cat["count"], EXPECTED_COUNT)
        self.assertEqual(len(self.skins), EXPECTED_COUNT)

    def test_meta(self):
        self.assertEqual(self.cat["owner"], OWNER)
        self.assertEqual(self.cat["repo"], "Genshen-Desktop-Skin")
        self.assertEqual(self.cat["pypi"], "genshen-desktop-skin")
        self.assertEqual(self.cat["cli"], "genshen-skin")
        self.assertIn("homepage", self.cat)
        self.assertIn("generated_at", self.cat)

    def test_two_copies_identical(self):
        """仓库根目录与包内各有一份 catalog.json，内容必须一致。"""
        import json
        pkg = os.path.join(ROOT, "genshen_skins", "catalog.json")
        root = os.path.join(ROOT, "catalog.json")
        self.assertTrue(os.path.exists(pkg), "缺少 genshen_skins/catalog.json")
        self.assertTrue(os.path.exists(root), "缺少 catalog.json")
        with open(pkg, encoding="utf-8") as f:
            a = json.load(f)
        with open(root, encoding="utf-8") as f:
            b = json.load(f)
        self.assertEqual(a["skins"], b["skins"], "两份 catalog 的 skins 不一致")

    def test_required_fields(self):
        for s in self.skins:
            for k in REQUIRED_SKIN_FIELDS:
                self.assertIn(k, s, "%s 缺少字段 %s" % (s.get("id"), k))
            for k in REQUIRED_CAPS:
                self.assertIn(k, s["caps"], "%s.caps 缺少 %s" % (s["id"], k))
            for k in REQUIRED_PATH_KEYS:
                self.assertIn(k, s["paths"], "%s.paths 缺少 %s" % (s["id"], k))

    def test_ids_unique_and_sequential(self):
        ids = [s["id"] for s in self.skins]
        self.assertEqual(len(ids), len(set(ids)), "id 有重复: %s" % ids)
        self.assertEqual([s["no"] for s in self.skins], list(range(1, EXPECTED_COUNT + 1)))

    def test_repos_unique(self):
        repos = [s["repo"] for s in self.skins]
        self.assertEqual(len(repos), len(set(repos)), "repo 有重复")

    def test_urls_consistent(self):
        for s in self.skins:
            self.assertEqual(s["repo"], "Genshen-%s-Skin" % s["repo"][len("Genshen-"):-len("-Skin")])
            self.assertEqual(s["url"], "https://github.com/%s/%s" % (OWNER, s["repo"]))
            self.assertEqual(s["clone"], s["url"] + ".git")
            self.assertTrue(s["raw"].startswith("https://raw.githubusercontent.com/%s/" % OWNER))
            self.assertTrue(s["raw"].endswith("/" + s["repo"] + "/main"))

    def test_accents_are_hex(self):
        for s in self.skins:
            self.assertRegex(s["accent"], r"^#[0-9a-fA-F]{6}$",
                             "%s 的主题色不是 6 位十六进制: %r" % (s["id"], s["accent"]))

    def test_char_names_nonempty(self):
        for s in self.skins:
            self.assertTrue(s["char"].strip(), "%s 角色名为空" % s["id"])
            self.assertTrue(s["name"].strip(), "%s 皮肤名为空" % s["id"])


class TestCapabilities(unittest.TestCase):
    """能力标记必须与 paths 自洽 —— 声称支持就必须有对应文件路径。"""

    def setUp(self):
        self.skins = cat_mod.load_catalog()["skins"]

    def test_dsh_cap_matches_client_path(self):
        for s in self.skins:
            self.assertEqual(
                bool(s["caps"]["dsh"]), bool(s["paths"]["dsh_client"]),
                "%s: caps.dsh=%s 但 dsh_client=%r"
                % (s["id"], s["caps"]["dsh"], s["paths"]["dsh_client"]))

    def test_desktop_cap_matches_scripts(self):
        for s in self.skins:
            has = bool(s["paths"]["desktop_ps1"]) and bool(s["paths"]["desktop_bat"])
            self.assertEqual(s["caps"]["desktop"], has, "%s 桌宠能力与路径不一致" % s["id"])

    def test_vscode_cap_matches_vsix(self):
        for s in self.skins:
            self.assertEqual(bool(s["caps"]["vscode"]), bool(s["paths"]["vsix"]),
                             "%s VSIX 能力与路径不一致" % s["id"])
            if s["caps"]["vscode"]:
                self.assertTrue(s["paths"]["vsix"].endswith(".vsix"))
                self.assertIn("ext", s, "%s 有 VSIX 却没有扩展信息" % s["id"])
                self.assertTrue(s["ext"]["id"], "%s 扩展 ID 为空" % s["id"])

    def test_capability_flags_are_bool(self):
        for s in self.skins:
            for k, v in s["caps"].items():
                self.assertIsInstance(v, bool, "%s.caps.%s 不是布尔值" % (s["id"], k))

    def test_every_skin_has_at_least_one_target(self):
        for s in self.skins:
            self.assertTrue(any(s["caps"].values()),
                            "%s 没有任何可安装目标" % s["id"])

    def test_known_gaps_are_documented(self):
        """刻晴目前缺 VSIX 与桌宠脚本；这个缺口必须被如实记录而不是悄悄消失。

        如果上游仓库补齐了，这个测试会失败 —— 提醒去更新文档说明。
        """
        kq = cat_mod.find_skin(cat_mod.load_catalog(), "keqing")
        self.assertIsNotNone(kq)
        self.assertFalse(kq["caps"]["vscode"], "刻晴已补上 VSIX？请更新 README 的说明")
        self.assertFalse(kq["caps"]["desktop"], "刻晴已补上桌宠？请更新 README 的说明")
        self.assertTrue(kq["caps"]["dsh"], "刻晴应至少支持 DSH")
        self.assertTrue(kq["notes"], "有缺口的皮肤必须写 notes")


class TestAssets(unittest.TestCase):
    def setUp(self):
        self.skins = cat_mod.load_catalog()["skins"]

    def test_wallpaper_paths_live_under_asset_dir(self):
        for s in self.skins:
            assets = s["paths"]["assets"]
            self.assertTrue(assets, "%s 没有素材目录" % s["id"])
            for w in s["wallpapers"]:
                self.assertTrue(w.startswith(assets + "/"),
                                "%s 的壁纸 %r 不在素材目录 %r 下" % (s["id"], w, assets))

    def test_wallpaper_extensions(self):
        for s in self.skins:
            for w in s["wallpapers"]:
                self.assertRegex(w.lower(), r"\.(jpg|jpeg|png)$", "%s: %r" % (s["id"], w))

    def test_voice_extensions(self):
        for s in self.skins:
            for v in s["voices"]:
                self.assertRegex(v.lower(), r"\.(mp3|wav|ogg)$", "%s: %r" % (s["id"], v))

    def test_wallpaper_count_reasonable(self):
        for s in self.skins:
            self.assertGreaterEqual(len(s["wallpapers"]), 1, "%s 一张壁纸都没有" % s["id"])
            self.assertLessEqual(len(s["wallpapers"]), 12, "%s 壁纸异常多" % s["id"])

    def test_dsh_assets_dir_matches_client_dir(self):
        for s in self.skins:
            client = s["paths"]["dsh_client"]
            assets = s["paths"]["dsh_assets"]
            self.assertTrue(assets, "%s 没有 dsh_assets" % s["id"])
            parent = client.rsplit("/", 1)[0] if "/" in client else ""
            expected = (parent + "/素材") if parent else "素材"
            self.assertEqual(assets, expected,
                             "%s: dsh_assets=%r 与 client=%r 不匹配" % (s["id"], assets, client))


class TestDshPrefix(unittest.TestCase):
    """cordis_define 的 idPrefix 必须是 3–6 位小写英文字母，且互不重复。"""

    def setUp(self):
        self.skins = cat_mod.load_catalog()["skins"]

    def test_prefix_format(self):
        for s in self.skins:
            p = dsh.prefix(s)
            self.assertRegex(p, r"^[a-z]{3,6}$", "%s 的 idPrefix %r 不合法" % (s["id"], p))

    def test_prefix_unique(self):
        seen = {}
        for s in self.skins:
            p = dsh.prefix(s)
            self.assertNotIn(p, seen, "%s 与 %s 的 idPrefix 都是 %r" % (s["id"], seen.get(p), p))
            seen[p] = s["id"]

    def test_prefix_stable(self):
        """同一套皮肤多次调用必须得到同样的前缀（否则重装会产生第二个插件）。"""
        for s in self.skins:
            self.assertEqual(dsh.prefix(s), dsh.prefix(s))


class TestSearch(unittest.TestCase):
    """AI / 用户会用中文名、英文名、拼音、别名、元素来找皮肤。"""

    def setUp(self):
        self.cat = cat_mod.load_catalog()

    def _find(self, key):
        s = cat_mod.find_skin(self.cat, key)
        return s["id"] if s else None

    def test_lookup_by_id(self):
        self.assertEqual(self._find("skirk"), "skirk")
        self.assertEqual(self._find("furina"), "furina")

    def test_lookup_by_repo(self):
        self.assertEqual(self._find("Genshen-Skirk-Skin"), "skirk")

    def test_lookup_by_chinese(self):
        self.assertEqual(self._find("丝柯克"), "skirk")
        self.assertEqual(self._find("芙宁娜"), "furina")
        self.assertEqual(self._find("刻晴"), "keqing")
        self.assertEqual(self._find("雷电将军"), "shogun")

    def test_lookup_by_english(self):
        self.assertEqual(self._find("Kamisato Ayaka"), "ayaka")
        self.assertEqual(self._find("Raiden Shogun"), "shogun")

    def test_lookup_by_alias(self):
        self.assertEqual(self._find("水神"), "furina")
        self.assertEqual(self._find("草神"), "nahida")
        self.assertEqual(self._find("旅行者"), "lumine")

    def test_lookup_by_number(self):
        """序号查询：目录里的第 N 套。"""
        first = self.cat["skins"][0]
        self.assertEqual(self._find("1"), first["id"])

    def test_lookup_case_insensitive(self):
        self.assertEqual(self._find("SKIRK"), "skirk")
        self.assertEqual(self._find("Furina"), "furina")

    def test_unknown_returns_none(self):
        self.assertIsNone(cat_mod.find_skin(self.cat, "这个角色不存在"))

    def test_empty_key_returns_default(self):
        self.assertIsNone(cat_mod.find_skin(self.cat, ""))
        self.assertEqual(cat_mod.find_skin(self.cat, "", default="x"), "x")

    def test_every_skin_findable_by_own_name(self):
        for s in self.cat["skins"]:
            got = cat_mod.find_skin(self.cat, s["char"])
            self.assertIsNotNone(got, "角色名查不到: %s" % s["char"])
            self.assertEqual(got["id"], s["id"],
                             "角色名 %r 查到了错误的皮肤 %r" % (s["char"], got["id"]))


class TestVersionConsistency(unittest.TestCase):
    """版本号散落在三处，必须一致，否则发出去的包版本会与代码自称的不符。"""

    def _read(self, rel):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return f.read()

    def test_versions_match(self):
        import re
        from genshen_skins import __version__ as pkg_version

        pyproject = self._read("pyproject.toml")
        m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
        self.assertIsNotNone(m, "pyproject.toml 里找不到 version")
        setup_py = self._read("setup.py")
        m2 = re.search(r'version\s*=\s*"([^"]+)"', setup_py)
        self.assertIsNotNone(m2, "setup.py 里找不到 version")

        self.assertEqual(pkg_version, m.group(1),
                         "__init__.py 与 pyproject.toml 版本不一致")
        self.assertEqual(pkg_version, m2.group(1),
                         "__init__.py 与 setup.py 版本不一致")

    def test_version_is_pep440(self):
        import re
        from genshen_skins import __version__ as v
        self.assertRegex(v, r"^\d+\.\d+\.\d+([ab]\d+|rc\d+)?$", "版本号不符合 PEP 440: %r" % v)


class TestRepoConsistency(unittest.TestCase):
    """README 里那张表和 catalog 必须一致，避免文档漂移。"""

    def test_readme_lists_all_repos(self):
        readme = os.path.join(ROOT, "README.md")
        if not os.path.exists(readme):
            self.skipTest("没有 README.md")
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        for s in cat_mod.load_catalog()["skins"]:
            self.assertIn(s["repo"], text, "README 里没有 %s" % s["repo"])
            self.assertIn("`%s`" % s["id"], text, "README 里没有 id %s" % s["id"])

    def test_no_placeholder_left_in_readme(self):
        readme = os.path.join(ROOT, "README.md")
        if not os.path.exists(readme):
            self.skipTest("没有 README.md")
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("CATALOG_TABLE", text, "README 里的目录表占位符没被替换")


if __name__ == "__main__":
    unittest.main(verbosity=2)
