# -*- coding: utf-8 -*-
"""Pillow 自动安装策略测试（完全不联网、不真的装包）。

背景：`ensure_pillow()` 原来固定带 `--user`。这个参数在 venv / conda 环境里
必然失败（`Can not perform a '--user' install.`），导致"看着在装、其实没装上"，
导出壁纸直接报「缺少 Pillow」。用户如果在虚拟环境里跑安装器就会撞上。

这里把 pip 调用与 `have_pillow()` 都换成桩，只验证**策略选择**：
  * venv / conda            → 不能带 `--user`
  * 系统 Python             → 先试 `--user`，失败再退回系统安装
  * PEP 668 外部管理环境    → 必须补 `--break-system-packages`
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genshen_skins import wallpaper  # noqa: E402


class _Recorder(object):
    """记录每次 pip 调用；按预设脚本决定成功与否。"""

    def __init__(self, fail_markers=()):
        self.calls = []
        self.fail_markers = list(fail_markers)

    def __call__(self, args, env=None):
        self.calls.append(list(args))
        joined = " ".join(args)
        for m in self.fail_markers:
            if m in joined:
                raise wallpaper.subprocess.CalledProcessError(1, args)
        return 0

    def flags(self):
        return [" ".join(c[3:]) for c in self.calls]


class PillowPolicyTest(unittest.TestCase):

    def setUp(self):
        self._have = wallpaper.have_pillow
        self._venv = wallpaper._in_venv
        self._pip = wallpaper.subprocess.check_call
        self._env = wallpaper.proxy.env_with_proxy
        wallpaper.proxy.env_with_proxy = lambda: {}
        # 装完即视为可用，模拟真实成功路径
        self.pillow_ok = [False]
        wallpaper.have_pillow = lambda: self.pillow_ok[0]

    def tearDown(self):
        wallpaper.have_pillow = self._have
        wallpaper._in_venv = self._venv
        wallpaper.subprocess.check_call = self._pip
        wallpaper.proxy.env_with_proxy = self._env

    def _run(self, in_venv, fail_markers=(), ok_after=1):
        rec = _Recorder(fail_markers)
        wallpaper.subprocess.check_call = rec
        wallpaper._in_venv = lambda: in_venv

        def fake(args, env=None):
            r = rec(args, env)
            if len(rec.calls) >= ok_after:
                self.pillow_ok[0] = True
            return r

        wallpaper.subprocess.check_call = fake
        result = wallpaper.ensure_pillow(quiet=True)
        return result, rec

    def test_venv_never_passes_user_flag(self):
        """venv 里带 --user 必失败 —— 这是本次修复的核心。"""
        ok, rec = self._run(in_venv=True)
        self.assertTrue(ok, "venv 下应安装成功")
        self.assertEqual(len(rec.calls), 1, "venv 下不该有多种尝试")
        self.assertNotIn("--user", rec.calls[0],
                         "venv 下不得带 --user：%s" % rec.flags())

    def test_system_python_prefers_user_install(self):
        """系统 Python 优先 --user，避免污染系统 site-packages。"""
        ok, rec = self._run(in_venv=False)
        self.assertTrue(ok)
        self.assertIn("--user", rec.calls[0], "系统 Python 应先试 --user")

    def test_falls_back_when_user_install_fails(self):
        """--user 失败（如被 PEP 668 拦）时必须有后续尝试，不能直接放弃。"""
        ok, rec = self._run(in_venv=False, fail_markers=["--user"], ok_after=2)
        self.assertTrue(ok, "第一次失败后应换方式重试")
        self.assertGreaterEqual(len(rec.calls), 2)
        self.assertIn("--user", rec.calls[0])
        self.assertNotIn("--user", rec.calls[1], "第二次尝试不该再带 --user")

    def test_break_system_packages_available_as_last_resort(self):
        """PEP 668 环境：最后的兜底必须显式带 --break-system-packages。"""
        ok, rec = self._run(in_venv=False, ok_after=3)
        self.assertTrue(ok, "兜底方式应能成功")
        joined = [" ".join(c) for c in rec.calls]
        self.assertTrue(any("--break-system-packages" in j for j in joined),
                        "缺少 --break-system-packages 兜底：%s" % joined)

    def test_gives_up_cleanly_when_all_attempts_fail(self):
        """全都失败时返回 False（而不是抛异常），让调用方给出可读提示。"""
        rec = _Recorder()
        wallpaper.subprocess.check_call = lambda a, env=None: (_ for _ in ()).throw(
            wallpaper.subprocess.CalledProcessError(1, a))
        wallpaper._in_venv = lambda: False
        self.assertFalse(wallpaper.ensure_pillow(quiet=True))

    def test_skips_install_when_already_present(self):
        """已装好时不该调用 pip。"""
        self.pillow_ok[0] = True
        rec = _Recorder()
        wallpaper.subprocess.check_call = rec
        wallpaper._in_venv = lambda: False
        self.assertTrue(wallpaper.ensure_pillow(quiet=True))
        self.assertEqual(rec.calls, [], "已有 Pillow 却仍去装包")


class InVenvDetectTest(unittest.TestCase):
    """`_in_venv()` 的真机判定（用真实解释器状态，不做桩）。"""

    def test_real_venv_is_detected(self):
        real = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        has_cfg = os.path.exists(os.path.join(sys.prefix, "pyvenv.cfg"))
        expected = real or has_cfg or bool(os.environ.get("CONDA_PREFIX"))
        self.assertEqual(wallpaper._in_venv(), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
