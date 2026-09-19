# 原神桌面皮肤集合 · Genshen Desktop Skin

**29 套原神角色动态皮肤，一个入口，按环境自动安装。**

把本仓库地址交给任意一个有本机权限的 AI 助手（DeepSeek Harness / claude-code / kimi-code /
CodeX / Trae / Cursor 等），说一句「装丝柯克皮肤」，AI 就会读
[AGENTS.md](AGENTS.md) 自动识别环境并装好。

```text
请安装 https://github.com/WPH666-py/Genshen-Desktop-Skin 的芙宁娜皮肤
```

支持 **DeepSeek Harness（DSH 动态插件）· VSCode · Trae · CodeX · Cursor · Windsurf ·
PyCharm / IntelliJ / WebStorm · claude-code · kimi-code · DeepKing · Windows 桌面桌宠**。

> 素材版权归米哈游（miHoYo / HoYoverse），仅供个人学习娱乐，请勿商用。

---

## 三种安装方式

### ① pip 一条命令（推荐）

```bash
pip install genshen-desktop-skin     # 国内网络见下方「镜像」

genshen-skin list                    # 看全部 29 套
genshen-skin install furina          # 一键：壁纸 + IDE 扩展 + 桌宠
genshen-skin wallpaper furina 2      # 只换壁纸（第 2 张）
genshen-skin pet keqing              # 只要桌面桌宠
genshen-skin env                     # 看看本机识别到了什么
genshen-skin                         # 不带参数 = 打印全部命令总览
```

**装完不确定能用什么命令？直接敲 `genshen-skin`（不带参数）** —— 会打印一份按用途
分组的完整命令总览（看目录 / 装·卸 / 单平台 / 镜像同步 / 诊断），每个命令的常用参数
和示例都在里面。也可以用 `genshen-skin commands`（别名 `help`、`?`）。
全局安装并立刻查看：

```bash
pip install --upgrade genshen-desktop-skin && genshen-skin
```

`install` 会自动做三件事，并跳过本机不支持的部分：

1. 拉取该套皮肤、按你的**屏幕分辨率**合成壁纸并设为桌面背景
   （默认 `blur` 适配：立绘完整显示，两侧用同图模糊填充，没有黑边）；
2. 给检测到的编辑器装 VSIX 扩展（VSCode / Trae / CodeX / Cursor / Windsurf / VSCodium）；
3. 启动 Windows 桌面置顶桌宠（悬浮于**所有**窗口之上，覆盖 PyCharm、claude-code、
   kimi-code、CodeX 等一切编辑器）。

#### 提示 `无法将“genshen-skin”项识别为 cmdlet…`？

装是成功的，只是 pip 的 `Scripts` 目录没在 `PATH` 里（pip 装完其实会打印一句
`...Scripts' which is not on PATH` 的警告）。三种解法，任选其一：

```powershell
# ① 最省事：用模块方式调用（模块名是下划线 genshen_skins，不是连字符）
#    注：连字符写法 `python -m genshen-skin` 同样是有效的（见下方说明），两种随你
py -3 -m genshen_skins list
py -3 -m genshen-skin list

# ② 用完整路径直接调 exe
& "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\genshen-skin.exe" list

# ③ 永久把 Scripts 加进 PATH（之后重开终端，genshen-skin 就能直接用）
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LOCALAPPDATA\Programs\Python\Python311\Scripts", "User")
```

> ⚠️ **上面 ② ③ 两条写法已作废（保留原文仅为留痕）**：里面写死的
> `%LOCALAPPDATA%\Programs\Python\Python311\Scripts` **只在你恰好也装的是 3.11 时才成立** ——
> 装 3.12 / 3.13 / conda / Store 版 Python 的用户照着抄会找不到文件，报「路径不存在」。
> 版本无关的正确写法是**从当前解释器推导路径**：
>
> ```powershell
> # ① 模块方式（用「你装包的那个 python」运行，3.8~3.13 任何版本都对）
> python -m genshen_skins list
> py -3 -m genshen_skins list          # Windows 装了 py 启动器时
> python3 -m genshen_skins list        # macOS / Linux
>
> # ② 打印你这个 python 的 Scripts 目录（exe 就在里面），再拿完整路径直接调
> python -c "import sys,os;print(os.path.dirname(sys.executable))"
>
> # ③ 永久加进用户 PATH（之后重开终端，genshen-skin 就能直接用）
> $s = python -c "import sys,os;print(os.path.dirname(sys.executable))"
> [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$s", "User")
> ```
>
> 另注：**`py -3` 永远挑版本最高的那个 python**，未必是你装包的那一个 ——
> 报 `No module named genshen_skins` 时先 `py -0p` 列出本机全部版本，
> 再用 `python -m pip show genshen-desktop-skin` 确认当前这个里到底有没有。
> 一句话：**用哪个 python 装的，就用哪个 python 跑。**

> `python -m genshen_skins` 与 `genshen-skin` **完全等价**。PATH 没配好时优先用它 ——
> 本文档后面出现的 `genshen-skin` 都可以替换成 `python -m genshen_skins`。
> macOS / Linux 上同理，把 `python` 换成 `python3`。
>
> **五种写法完全等价**，挑顺手的用：
>
> | 写法 | 说明 |
> |---|---|
> | `genshen-skin list` | 控制台命令（PATH 配好后可用） |
> | `gss list` | 上面那个的短别名 |
> | `python -m genshen-skin list` | **连字符也合法** |
> | `python -m genshen_skin list` | 下划线单数 |
> | `python -m genshen_skins list` | 下划线复数（正式包名） |
>
> 关于连字符：`python -m` 是按**字符串**在 `sys.path` 里找模块的，**不要求名字是
> 合法标识符**，所以带连字符的入口文件能被找到并执行。包里因此专门放了
> `genshen-skin.py` 与 `genshen_skin.py` 两个顶层入口。
> 只有 `import genshen-skin` 这种**语句**形式才是语法错误 —— 两回事，别混。

### ② 给 AI 一句话

见顶部示例。AI 读取 `catalog.json`（29 套的能力矩阵）与 `AGENTS.md`（分环境安装指引），
不需要你懂任何命令。

### ③ 手动克隆

```bash
git clone https://github.com/WPH666-py/Genshen-Furina-Skin
```

每个皮肤仓库都有自己的 `AGENTS.md` / `README.md` / `dsh-plugin/` / `vscode-extension/` /
`desktop/`，可单独使用。

---

## 国内镜像

PyPI 镜像（清华、中科大都是 PyPI 的只读镜像，自动同步）：

> 阿里云 / 腾讯云同样是只读镜像。`genshen-skin mirror` 会把**四个国内源**的装包命令
> 与「怎么确认镜像已经同步」一起列出来；`genshen-skin doctor` 会逐个**实测**，
> 直接给出当前网络下能用的那一条。

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple genshen-desktop-skin   # 清华 TUNA
pip install -i https://mirrors.ustc.edu.cn/pypi/simple genshen-desktop-skin    # 中科大 USTC
pip install -i https://mirrors.aliyun.com/pypi/simple genshen-desktop-skin     # 阿里云
pip install -i https://mirrors.cloud.tencent.com/pypi/simple genshen-desktop-skin   # 腾讯云
genshen-skin mirror                                                            # 看全部镜像
```

GitHub 加速（克隆皮肤仓库 / 下载 raw 文件时自动依次尝试，无需手动配置）：

| 通道 | 用途 |
|---|---|
| 直连 GitHub | clone / raw |
| jsDelivr CDN | raw |
| ghfast.top | clone / raw |
| gitmirror | clone / raw |
| gh-proxy.com / ghproxy.net | clone / raw |

代理也会自动探测：桌面代理软件通常只设 Windows 系统代理（git 能读、pip 读不到），
本工具会把探测到的代理显式传给 git 与 pip。`GENSHEN_NO_PROXY=1` 关闭，
`GENSHEN_PROXY=http://host:port` 手动指定。体检：`genshen-skin doctor`。

---

## 全部命令

| 命令 | 作用 |
|---|---|
| `genshen-skin list` | 列出 29 套皮肤与各自可用环境 |
| `genshen-skin show <角色>` | 查看某套的详情、壁纸、安装方式 |
| `genshen-skin install <角色>` | 一键安装（壁纸 + 扩展 + 桌宠） |
| `genshen-skin wallpaper <角色> [1\|2\|3\|random]` | 切换桌面壁纸 |
| `genshen-skin export <角色> [--out 目录]` | 导出全部分辨率壁纸（PyCharm 背景图用） |
| `genshen-skin pet <角色>` | 桌面桌宠：`--stop` / `--autostart` / `--no-autostart` / `--uninstall` |
| `genshen-skin ide <角色>` | 装 VSIX 扩展；`--list` 看检测到的编辑器，`--uninstall` 卸载 |
| `genshen-skin dsh <角色>` | 生成 DSH 动态插件载荷 + 操作单 |
| `genshen-skin deepking <角色>` | 导出 DeepKing 皮肤规范包 |
| `genshen-skin sync --all` | 把 29 个仓库克隆到 `~/.genshen-skins` |
| `genshen-skin vendor --out <目录>` | 把 29 个仓库全部落地到指定目录（离线收藏） |
| `genshen-skin env` / `doctor` / `paths` | 环境 / 体检 / 本地目录 |
| `genshen-skin mirror [--set tuna\|ustc]` | 查看 / 设置镜像 |
| `genshen-skin uninstall <角色>` | 卸载（扩展 + 桌宠 + 自启 + 本地副本） |

角色可以用中文名、英文名、拼音或别名：`genshen-skin show 雷神`、`show shogun`、
`show 草神`、`show furina` 都能命中。

本地文件都在 `~/.genshen-skins/`（`GENSHEN_HOME` 可改），不会污染你的项目目录。

---

## 皮肤目录（29 套）

| # | ID | 皮肤 | 角色 | 元素 | 主题色 | 壁纸 | DSH | IDE扩展 | 桌宠 | DeepKing | 仓库 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `citlali` | 茜特拉莉 · 紫粉星夜 | 茜特拉莉 | 冰 | `#a855f7` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Citlali-Skin](https://github.com/WPH666-py/Genshen-Citlali-Skin) |
| 2 | `skirk` | 丝柯克 · 霜刃渊海 | 丝柯克 | 冰 | `#5f8cff` | 1 | ✅ | ✅ | ✅ | ✅ | [Genshen-Skirk-Skin](https://github.com/WPH666-py/Genshen-Skirk-Skin) |
| 3 | `keqing` | 刻晴 · 紫电雷鸣 | 刻晴 | 雷 | `#8b5cf6` | 3 | ✅ | — | — | ✅ | [Genshen-Keqing-Skin](https://github.com/WPH666-py/Genshen-Keqing-Skin) |
| 4 | `furina` | 芙宁娜 · 深蓝咏叹 | 芙宁娜 | 水 | `#3d9dc9` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Furina-Skin](https://github.com/WPH666-py/Genshen-Furina-Skin) |
| 5 | `hutao` | 胡桃 · 焰蝶飞白 | 胡桃 | 火 | `#d92b1e` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Hutao-Skin](https://github.com/WPH666-py/Genshen-Hutao-Skin) |
| 6 | `kokomi` | 心海 · 海月之誓 | 珊瑚宫心海 | 水 | `#3b8fd4` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Kokomi-Skin](https://github.com/WPH666-py/Genshen-Kokomi-Skin) |
| 7 | `ayaka` | 绫华 · 霜雪冰刃 | 神里绫华 | 冰 | `#5a8fe0` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Ayaka-Skin](https://github.com/WPH666-py/Genshen-Ayaka-Skin) |
| 8 | `yoimiya` | 宵宫 · 琉金云间草 | 宵宫 | 火 | `#d9584a` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Yoimiya-Skin](https://github.com/WPH666-py/Genshen-Yoimiya-Skin) |
| 9 | `lumine` | 荧 · 六元素随机 | 荧 | - | `#4a8fd8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Lumine-Skin](https://github.com/WPH666-py/Genshen-Lumine-Skin) |
| 10 | `shenhe` | 申鹤 · 神女遣灵真诀 | 申鹤 | 冰 | `#5a90d8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Shenhe-Skin](https://github.com/WPH666-py/Genshen-Shenhe-Skin) |
| 11 | `eula` | 优菈 · 凝浪之光剑 | 优菈 | 冰 | `#5a90e0` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Eula-Skin](https://github.com/WPH666-py/Genshen-Eula-Skin) |
| 12 | `sucrose` | 砂糖 · 禁·风灵作成·柒伍式 | 砂糖 | 风 | `#e09c40` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Sucrose-Skin](https://github.com/WPH666-py/Genshen-Sucrose-Skin) |
| 13 | `nicole` | 尼可 · 圣言默示·天路历程 | 尼可 | - | `#4a8fd8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Nicole-Skin](https://github.com/WPH666-py/Genshen-Nicole-Skin) |
| 14 | `barbara` | 芭芭拉 · 闪耀奇迹 | 芭芭拉 | 水 | `#4a90d8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Barbara-Skin](https://github.com/WPH666-py/Genshen-Barbara-Skin) |
| 15 | `collei` | 柯莱 · 猫猫秘宝 | 柯莱 | 草 | `#62a83e` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Collei-Skin](https://github.com/WPH666-py/Genshen-Collei-Skin) |
| 16 | `nilou` | 妮露 · 浮莲舞步·远梦聆泉 | 妮露 | 水 | `#3f9fc9` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Nilou-Skin](https://github.com/WPH666-py/Genshen-Nilou-Skin) |
| 17 | `nahida` | 纳西妲 · 心景幻成 | 纳西妲 | 草 | `#4a9e46` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Nahida-Skin](https://github.com/WPH666-py/Genshen-Nahida-Skin) |
| 18 | `shogun` | 雷电将军 · 奥义·梦想真说 | 雷电将军 | 雷 | `#7a5ad8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Shogun-Skin](https://github.com/WPH666-py/Genshen-Shogun-Skin) |
| 19 | `ambor` | 安柏 · 箭雨 | 安柏 | 火 | `#d93a2e` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Ambor-Skin](https://github.com/WPH666-py/Genshen-Ambor-Skin) |
| 20 | `yelan` | 夜兰 · 玄掷玲珑 | 夜兰 | 水 | `#1f7fd4` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Yelan-Skin](https://github.com/WPH666-py/Genshen-Yelan-Skin) |
| 21 | `zibai` | 兹白 · 三垣威仪法 | 兹白 | - | `#2f9e78` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Zibai-Skin](https://github.com/WPH666-py/Genshen-Zibai-Skin) |
| 22 | `ganyu` | 甘雨 · 降众天华 | 甘雨 | 冰 | `#5a8fe0` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Ganyu-Skin](https://github.com/WPH666-py/Genshen-Ganyu-Skin) |
| 23 | `columbina` | 哥伦比娅 · 她的乡愁 | 哥伦比娅 | - | `#7a5fd8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Columbina-Skin](https://github.com/WPH666-py/Genshen-Columbina-Skin) |
| 24 | `linnea` | 莉奈娅 · 备忘·绝境生存指南 | 莉奈娅 | - | `#d94a68` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Linnea-Skin](https://github.com/WPH666-py/Genshen-Linnea-Skin) |
| 25 | `escoffier` | 爱可菲 · 花刀技法 | 爱可菲 | 冰 | `#3fb8e0` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Escoffier-Skin](https://github.com/WPH666-py/Genshen-Escoffier-Skin) |
| 26 | `navia` | 娜维娅 · 如霰澄天的鸣礼 | 娜维娅 | 岩 | `#c8962c` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Navia-Skin](https://github.com/WPH666-py/Genshen-Navia-Skin) |
| 27 | `mualani` | 玛拉妮 · 爆瀑飞弹 | 玛拉妮 | 水 | `#2f9fd8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Mualani-Skin](https://github.com/WPH666-py/Genshen-Mualani-Skin) |
| 28 | `sandrone` | 桑多涅 · 事象数式·万理证毕 | 桑多涅 | - | `#a02838` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Sandrone-Skin](https://github.com/WPH666-py/Genshen-Sandrone-Skin) |
| 29 | `clorinde` | 克洛琳德 · 秉烛剔星月 | 克洛琳德 | 雷 | `#7a5fd8` | 3 | ✅ | ✅ | ✅ | ✅ | [Genshen-Clorinde-Skin](https://github.com/WPH666-py/Genshen-Clorinde-Skin) |

`壁纸` 列是该套可切换的壁纸张数；`—` 表示该皮肤仓库暂未提供对应形态
（目前只有刻晴缺 VSIX 与桌宠脚本 —— `genshen-skin pet keqing` 会用内置通用桌宠补上）。

完整机器可读目录见 [catalog.json](catalog.json)（含每套的真实文件路径、扩展 ID、
命令 ID、壁纸清单与能力矩阵）。皮肤仓库有更新时，重跑
`python scripts/sync_catalog.py` 即可刷新整张矩阵。

---

## 仓库结构

```
Genshen-Desktop-Skin/
├── AGENTS.md              ← AI 助手自动安装指引（核心）
├── README.md              ← 本文件
├── catalog.json           ← 29 套皮肤机器可读目录（能力矩阵/路径/扩展ID/壁纸）
├── pyproject.toml         ← PyPI 包定义
├── genshen_skins/         ← 安装器 Python 包
│   ├── cli.py             git/genshen-skin 命令行
│   ├── catalog.py         目录检索（中文名/英文名/拼音/别名/元素）
│   ├── repo.py            克隆与单文件下载（含镜像回退、代理注入）
│   ├── proxy.py           本机代理自动探测
│   ├── mirror.py          PyPI 镜像 + GitHub 加速通道
│   ├── wallpaper.py       壁纸合成与跨平台设置
│   ├── targets.py         IDE 检测与 VSIX 安装
│   ├── desktop.py         桌宠部署/启动/自启/卸载
│   ├── dsh.py             DSH 动态插件载荷
│   └── assets/
│       └── genshen-pet.ps1   内置通用桌宠（给没有自带桌宠的皮肤用）
├── scripts/
│   ├── sync_catalog.py    从 GitHub 重新生成 catalog.json
│   └── vendor_all.py      把 29 个仓库全部落地到本地
└── docs/
    ├── INSTALL.md         分环境详细安装说明与排错
    └── MIRRORS.md         清华 / 中科大镜像说明
```

---

## 设计取舍

- **本仓库不含素材**，只放目录与安装器（< 1 MB）。素材按需从 29 个皮肤仓库拉取：
  单套皮肤更新后立刻生效，不必重推一个大仓库。想一次性全部落地用
  `genshen-skin vendor --out <目录>`。
- **能力矩阵是实测出来的**，不是手写的：`scripts/sync_catalog.py` 读每个仓库的
  git tree、`skin.json`、`vscode-extension/package.json`，所以 `caps` 与 `paths`
  始终反映仓库真实内容（哪套缺 VSIX、哪套的 DSH 客户端在根目录，都如实记录）。
- **换壁纸不克隆整个仓库**：只下载用到的那几张 `-web.jpg`（一套通常 400 KB 左右），
  而 19 MB 的仓库不必为了换壁纸整份拉下来。

---

## 验证状态

不靠"看起来能跑"，下面都是实际跑过的：

**自动化（`python -m unittest discover -s tests -t .`，94 个用例，零依赖）**

- catalog 自洽性：字段齐全、能力标记必须与文件路径一致（声称支持就得有对应文件）、
  `idPrefix` 合法且互不重复、壁纸路径归属于素材目录、仓库根目录与包内两份 catalog 一致
- 检索：中文名 / 英文名 / 别名（水神、草神、旅行者）/ 元素 / 序号 / 大小写
- VSIX 全链路：读扩展 ID → 解压安装 → 覆盖安装（旧文件不残留）→ 卸载 → 损坏文件处理
- 壁纸模式解析、镜像 URL 拼装、Windows 只读文件删除、三处版本号一致、README 与 catalog 不漂移

**CI（[GitHub Actions](https://github.com/WPH666-py/Genshen-Desktop-Skin/actions)）**

- Windows / macOS / Ubuntu × Python 3.8 / 3.11 / 3.12，9 个组合全绿

> ⚠️ **上面这行已过期（保留原文仅为留痕）**，1.0.8 起实际情况是：
>
> - 测试用例 **94 → 124 个**（`python -m unittest discover -s tests -t .`，零依赖）
> - CI 矩阵 **9 → 18 个组合**：Windows / macOS / Ubuntu × **Python 3.8 / 3.9 / 3.10 / 3.11 / 3.12 / 3.13**
> - 新增 `smoke` 作业：用 `python -m build` 打出来的 **wheel 发布产物**，在 3.8~3.13 上
>   **逐个 `pip install` 再真跑一次**（`genshen-skin list`、`python -m genshen_skins list`、
>   `python -m genshen-skin list`、`gss list` 四种入口都跑）——
>   「不管用户装的是哪个 Python 3 都能用」这条承诺由它守着。
>
>   为什么非要这样：单版本开发机上「一切正常」毫无意义 —— 本项目就出过一次
>   **pip 装成功、第一条命令就崩** 的事故（`importlib.resources.files()` 是 3.9+ 的 API，
>   而声明的是 `requires-python >= 3.8`；3.8 上 `AttributeError`）。只有跑矩阵才看得见。
- 额外校验：wheel 内含 catalog 与桌宠脚本、**桌宠脚本的 UTF-8 BOM 未丢**（丢了会让
  Windows PowerShell 5.1 按 GBK 解析、中文全乱）、装好轮子后在仓库外冒烟
- 每周定时比对上游皮肤仓库，catalog 落后时提醒重跑 `scripts/sync_catalog.py`

**真机实测（Windows）**

- 壁纸：真实设置系统壁纸成功；按 3072×1920 真实物理分辨率合成，立绘完整居中、
  两侧同色系模糊填充、无黑边
- DSH：芙宁娜 609 KB 载荷下载完整、4 处内嵌素材、未截断
- 桌宠：进程起得来、可跨命令存活、`.pid` 与真实进程一致、窗口 `visible/TOPMOST/在屏内`；
  被宿主 Job 回收导致秒退的问题已改走 explorer 启动解决
- 克隆：`sync --all` 29/29 成功（259 MB，173 秒），镜像回退生效
- PyPI：全新 venv 从官方源与清华源各装一次并冒烟通过

> 已知环境限制：在虚拟化桌面（无 DWM 合成的远程/无头会话）里，WPF 分层窗口不会被绘制。
> 用仓库自带的定制桌宠脚本做过对照，表现相同，因此这是环境限制而非本项目的问题。
> 普通 Windows 桌面不受影响。

---

## 版权

安装器与脚本文档以 [MIT](LICENSE) 发布。

立绘、壁纸、语音等素材版权归**米哈游（miHoYo / HoYoverse）**，语音台词与音频来自
[原神 BWIKI](https://wiki.biligame.com/ys/)。素材仅供个人学习与娱乐使用，
**不得用于商业用途**，不在 MIT 许可范围内。
