# -*- coding: utf-8 -*-
"""AGENTS.md 是「把仓库地址交给 AI 就能自动安装」这条路的合同文件。

它一旦缺失或被删改，AI 助手就失去分环境安装的依据（只剩 README 可猜），
所以这里把它的存在与必备内容固定下来 —— 以后谁误删了 CI 会立刻报出来。
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(ROOT, "AGENTS.md")


class TestAgentsMd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(AGENTS):
            raise unittest.SkipTest("没有 AGENTS.md")
        with open(AGENTS, encoding="utf-8") as f:
            cls.text = f.read()

    def test_exists_and_not_a_stub(self):
        self.assertTrue(os.path.exists(AGENTS), "AGENTS.md 缺失 —— AI 自动安装就没了依据")
        self.assertGreater(len(self.text.encode("utf-8")), 3000,
                           "AGENTS.md 太短，不像是完整指引")

    def test_is_valid_utf8_without_bom(self):
        """Markdown 不需要 BOM；带 BOM 会让某些渲染器把首行标题吃掉。"""
        with open(AGENTS, "rb") as f:
            head = f.read(3)
        self.assertNotEqual(head, b"\xef\xbb\xbf", "AGENTS.md 不应带 UTF-8 BOM")

    def test_covers_every_promised_environment(self):
        """用户明确点名要支持的每种环境都必须在指引里有对应做法。"""
        required = {
            "DeepSeek Harness": ["cordis_define", "cordis_run"],
            "VSCode": ["--install-extension"],
            "Trae": ["Trae"],
            "CodeX": ["CodeX"],
            "Cursor": ["Cursor"],
            "PyCharm / JetBrains": ["PyCharm", "Background Image"],
            "claude-code": ["claude-code"],
            "kimi-code": ["kimi-code"],
            "DeepKing": ["DeepKing"],
            "桌面桌宠": ["桌宠", "explorer"],
        }
        missing = []
        for label, needles in required.items():
            for n in needles:
                if n not in self.text:
                    missing.append("%s -> 缺少 %r" % (label, n))
        self.assertEqual(missing, [], "AGENTS.md 漏了这些环境/关键词:\n  " + "\n  ".join(missing))

    def test_mentions_both_chinese_mirrors(self):
        self.assertIn("pypi.tuna.tsinghua.edu.cn", self.text, "缺清华源")
        self.assertIn("mirrors.ustc.edu.cn", self.text, "缺中科大源")

    def test_mentions_github_accelerators(self):
        for host in ("jsDelivr", "ghfast", "gitmirror", "gh-proxy"):
            self.assertIn(host, self.text, "缺 GitHub 加速通道说明: %s" % host)

    def test_warns_about_base64_integrity(self):
        """素材是内嵌 base64 的，AI 一旦"美化格式"就会把皮肤弄坏。"""
        self.assertIn("base64", self.text)
        self.assertTrue(("不要换行" in self.text) or ("不要截断" in self.text),
                        "缺少「base64 不得增删改」的明确约束")

    def test_mentions_catalog_json_as_source_of_truth(self):
        self.assertIn("catalog.json", self.text)
        for key in ("caps", "paths", "raw"):
            self.assertIn(key, self.text, "没告诉 AI catalog 里的 %s 字段" % key)

    def test_mentions_copyright(self):
        self.assertTrue(("米哈游" in self.text) or ("miHoYo" in self.text),
                        "缺少素材版权说明")
        self.assertIn("不得商用", self.text)

    def test_mentions_uninstall(self):
        self.assertIn("uninstall", self.text)
        self.assertIn("cordis_undefine", self.text)

    def test_lists_all_34_characters(self):
        """角色关键词对照表必须覆盖全部 34 套，否则 AI 会漏掉一些皮肤。"""
        from genshen_skins import catalog as c
        missing = [s["char"] for s in c.load_catalog()["skins"] if s["char"] not in self.text]
        self.assertEqual(missing, [], "AGENTS.md 的角色对照表漏了: %s" % ", ".join(missing))

    def test_all_ids_referenced(self):
        from genshen_skins import catalog as c
        missing = [s["id"] for s in c.load_catalog()["skins"] if s["id"] not in self.text]
        self.assertEqual(missing, [], "AGENTS.md 没提到这些 id: %s" % ", ".join(missing))


class TestAgentsMdIsDiscoverable(unittest.TestCase):
    """AI 助手通常由 README / 仓库首页指向 AGENTS.md。"""

    def test_readme_points_to_agents_md(self):
        readme = os.path.join(ROOT, "README.md")
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("AGENTS.md", text, "README 没有指向 AGENTS.md，AI 可能找不到它")


if __name__ == "__main__":
    unittest.main(verbosity=2)
