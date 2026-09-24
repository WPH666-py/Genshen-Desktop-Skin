# MIRRORS.md — PyPI 镜像与 GitHub 加速

两件经常被混为一谈的事，分开讲清楚。

---

## 一、PyPI 镜像（清华 / 中科大 / 阿里 / 腾讯）：用于 `py -3 -m pip install`

| 别名 | 名称 | index-url |
|---|---|---|
| `tuna` | 清华大学 TUNA | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| `ustc` | 中国科学技术大学 USTC | `https://mirrors.ustc.edu.cn/pypi/simple` |
| `aliyun` | 阿里云 | `https://mirrors.aliyun.com/pypi/simple` |
| `tencent` | 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple` |
| `official` | PyPI 官方 | `https://pypi.org/simple` |

### 装本包

```powershell
py -3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple genshen-desktop-skin      # 清华
py -3 -m pip install -i https://mirrors.ustc.edu.cn/pypi/simple genshen-desktop-skin       # 中科大
py -3 -m pip install -i https://mirrors.aliyun.com/pypi/simple genshen-desktop-skin        # 阿里云
py -3 -m pip install -i https://mirrors.cloud.tencent.com/pypi/simple genshen-desktop-skin # 腾讯云
```

`py -3 -m genshen_skins doctor` 会实测这几个源哪个通，并直接给出可用的安装命令。
（macOS / Linux 把 `py -3` 换成 `python3`。）



### ⚠️ 关于「发布到清华源 / 中科大源」

**做不到，也不需要做。** 清华 TUNA 与中科大 USTC 的 PyPI 都是**只读镜像**：
它们定时从 `pypi.org` 拉取（`rsync` / `bandersnatch` 类同步），个人没有上传入口。

正确的流程只有一条：

```
作者 py -3 -m twine upload  ──►  pypi.org  ──(自动同步, 通常几分钟内)──►  清华 / 中科大 / 阿里 …
```

所以本项目的发布流程是「**发一次 PyPI，国内镜像自动收录**」。发布后可以用下面两个地址
确认镜像是否已经同步到（能打开、且版本号是最新的即可）：

- 清华：<https://pypi.tuna.tsinghua.edu.cn/simple/genshen-desktop-skin/>
- 中科大：<https://mirrors.ustc.edu.cn/pypi/simple/genshen-desktop-skin/>

同步有延迟时，先直接用官方源装，或稍后再试镜像。

### 想长期默认走镜像

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
```

或给本工具设一个默认镜像（影响它内部调用 pip 时用的源）：

```powershell
# 当前会话
$env:GENSHEN_MIRROR = "tuna"
# 永久（Windows 用户级）
[Environment]::SetEnvironmentVariable("GENSHEN_MIRROR", "tuna", "User")
```

---

## 二、GitHub 加速：用于 clone 皮肤仓库 / 下载 raw 文件

34 套皮肤仓库都在 GitHub 上。国内直连 `raw.githubusercontent.com` 经常超时，
`genshen-skin` 会**自动按顺序尝试**下列通道，第一个成功的会被记住，后续优先复用：

| 通道 | 说明 | 支持 |
|---|---|---|
| 直连 GitHub | 能通就用它，最快最可信 | clone + raw |
| jsDelivr CDN | `cdn.jsdelivr.net/gh/<owner>/<repo>@<branch>/<path>` | raw |
| ghfast.top | 前缀式加速 | clone + raw |
| gitmirror | `hub.gitmirror.com` / `raw.gitmirror.com` | clone + raw |
| gh-proxy.com | 前缀式加速 | clone + raw |
| ghproxy.net | 前缀式加速 | clone + raw |

clone 全部失败时还会退回 `codeload.github.com` 下载源码包并解压 —— 这样即使没装 git
也能拿到皮肤文件。

### 手动下载单个文件时，按这个顺序试

```bash
# 1) 直连
https://raw.githubusercontent.com/WPH666-py/Genshen-Furina-Skin/main/dsh-plugin/client-standalone.js

# 2) jsDelivr（国内通常最稳）
https://cdn.jsdelivr.net/gh/WPH666-py/Genshen-Furina-Skin@main/dsh-plugin/client-standalone.js

# 3) ghfast
https://ghfast.top/https://raw.githubusercontent.com/WPH666-py/Genshen-Furina-Skin/main/dsh-plugin/client-standalone.js
```

> jsDelivr 对单文件大小有限制（较大文件会拒绝），本项目最大的立绘约 7 MB，
> 正常范围内；实在不行换 ghfast / gitmirror。

### 克隆仓库

```bash
git clone https://github.com/WPH666-py/Genshen-Furina-Skin.git
# 走加速：
git clone https://ghfast.top/https://github.com/WPH666-py/Genshen-Furina-Skin.git
```

---

## 三、代理

桌面代理软件（Clash / verge / v2ray …）默认通常**只设 Windows 系统代理**：
git 读注册表所以能用，而 pip / Python urllib **不读注册表**，只认环境变量 ——
于是出现「git 能克隆但 pip 装不上」的怪现象。

`genshen-skin` 的 `proxy.py` 会按这个顺序探测并显式注入：

1. `GENSHEN_PROXY`（或 `DEEPSKINS_PROXY`）显式指定；
2. 环境变量 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`（含小写）；
3. Windows 注册表 `Internet Settings` 的系统代理（仅 `ProxyEnable=1` 时）；
4. 本机常见代理端口探测（7897 / 7890 / 7891 / 10809 / 1080 / 8888 / 2080 / 20171 / 33210）。

探测结果会同时传给 git（`-c http.proxy=…`，仅在用户没自配代理时）与 pip（`--proxy` + 环境变量）。
git 全局已经配了代理的话不会被覆盖。

```bash
py -3 -m genshen_skins doctor        # 看探测结果 + 各源可达性
GENSHEN_NO_PROXY=1         # 关闭探测
GENSHEN_PROXY=http://127.0.0.1:7897   # 手动指定
```
