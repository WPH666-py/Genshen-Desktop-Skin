# AGENTS.md — 原神桌面皮肤集合 · AI 自动安装指引（AI 助手必读）

用户把 **https://github.com/WPH666-py/Genshen-Desktop-Skin** 交给你，并说「装原神皮肤 / 桌面壁纸 /
换壁纸 / 装个桌宠」时，按本文件执行。

本仓库是 **30 套原神角色动态皮肤的集合**：机器可读目录 `catalog.json` + 跨平台安装器
（PyPI 包 `genshen-desktop-skin`，命令 `genshen-skin`）。
每套皮肤本身是一个独立仓库，本仓库负责「一套入口、按环境自动装到对的地方」。

---

## 第 0 步：先确认用户想要哪一套

- 用户点名了角色（「丝柯克」「芙宁娜」「雷神」「草神」…）→ 用 `py -3 -m genshen_skins show <关键词>` 确认，再装那一套。
- 用户说「全部 / 都装上」→ 见下方「全部安装」。
- 不确定是哪一套 → 读 `catalog.json` 的 `skins[].char` / `name` / `aliases` 匹配；
  匹配不到就列几个候选问用户。
- **不要**在没有确认的情况下给 30 套全部换壁纸（那是 29 次系统壁纸切换）。

角色关键词对照（部分）：丝柯克=skirk、芙宁娜=水神=furina、刻晴=keqing、胡桃=hutao、
心海=kokomi、绫华=神里=ayaka、宵宫=yoimiya、荧=旅行者=lumine、申鹤=shenhe、优菈=eula、
砂糖=sucrose、尼可=nicole、芭芭拉=barbara、柯莱=collei、妮露=nilou、纳西妲=草神=nahida、
雷电将军=雷神=影=shogun、安柏=amber=ambor、夜兰=yelan、兹白=zibai、甘雨=ganyu、
哥伦比娅=columbina、莉奈娅=linnea、爱可菲=escoffier、娜维娅=navia、玛拉妮=mualani、
桑多涅=sandrone、克洛琳德=clorinde、茜特拉莉=citlali、诺艾尔=noelle=女仆=西风骑士团。

（全名与简称都能命中：「珊瑚宫心海」与「心海」、「神里绫华」与「绫华」「神里」，
检索不区分大小写，也可以直接用目录序号，例如「第 7 套」。）

---

## 路线 A（首选）：pip 装安装器，一条命令搞定

安装器会自己识别本机环境（有哪些 IDE、有没有 DSH、屏幕多大、要不要走代理），
把皮肤装到所有该装的地方。

**统一调用格式：Windows 一律 `py -3 -m`，macOS / Linux 一律 `python3 -m`。**
这个形式不依赖 pip 的 `Scripts` 目录在不在 `PATH` 里，所以不需要教用户配 PATH。

```powershell
# 1) 装安装器（国内网络用镜像，见下）
py -3 -m pip install genshen-desktop-skin

# 2) 看有哪些皮肤
py -3 -m genshen_skins list

# 3) 装某一套（自动：生成并设置壁纸 + 给检测到的 IDE 装扩展 + 启动桌宠）
py -3 -m genshen_skins install skirk

# 其它常用
py -3 -m genshen_skins wallpaper furina 2      # 只换壁纸（第 2 张）
py -3 -m genshen_skins pet keqing              # 只要桌面桌宠
py -3 -m genshen_skins ide furina              # 只装 VSCode/Trae/CodeX 扩展
py -3 -m genshen_skins dsh furina              # 只要 DSH 动态插件载荷
py -3 -m genshen_skins export furina --out D:\skins   # 导出壁纸给 PyCharm 当背景图
py -3 -m genshen_skins env                     # 看本机识别到的环境
py -3 -m genshen_skins doctor                  # 网络/代理/镜像体检
```

**国内网络装不上 pip 包时**（pypi.org 连不上 / TLS 被中断），改用镜像 —— 三个都试一下：

```powershell
py -3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple genshen-desktop-skin   # 清华 TUNA
py -3 -m pip install -i https://mirrors.ustc.edu.cn/pypi/simple genshen-desktop-skin    # 中科大 USTC
py -3 -m pip install -i https://mirrors.aliyun.com/pypi/simple genshen-desktop-skin     # 阿里云
```

`py -3 -m genshen_skins doctor` 会实测 pypi.org / 清华 / 中科大 / 阿里哪个通，
并直接给出可用的安装命令。



### 调用格式：Windows 统一 `py -3 -m`，macOS / Linux 统一 `python3 -m`

```powershell
py -3 -m genshen_skins list          # Windows
python3 -m genshen_skins list        # macOS / Linux
```

**这个形式不依赖 pip 的 `Scripts` 目录在不在 `PATH` 里** —— 所以
「无法将"genshen-skin"项识别为 cmdlet」「command not found」这类报错，
改用上面的写法就没了，**不需要去配 PATH**。

- `py -3` 挑的是本机**版本最高**的 Python，未必是装了包的那个
  （症状：`No module named genshen_skins`）。先 `py -0p` 看全部版本，
  再用 `py -3 -m pip show genshen-desktop-skin` 确认当前这个里有没有；
  必要时指定版本，例如 `py -3.12 -m genshen_skins list`。
- **不要**照着 `...\Programs\Python\Python3<版本>\Scripts` 这类**写死版本**的路径去配
  `PATH` —— 那只在用户恰好也是那个版本时才成立（本项目踩过这个坑）。
- 连字符入口（`genshen-skin.py` / `genshen_skin.py`）包内同样保留、也仍然可用，
  但**文档统一只推 `genshen_skins`（下划线复数，正式包名）**一种。
- 三个名字别混：pip 发行名 `genshen-desktop-skin` / 模块名 `genshen_skins` / 命令名 `genshen-skin`。



**没有 Python 时**先装 Python —— **3.8 及以上任意版本都可以**（CI 覆盖 3.8~3.13）：

```powershell
winget install Python.Python.3.12     # Windows（3.8~3.13 任一版本都行）
brew install python                   # macOS
sudo apt install python3 python3-pil  # Ubuntu / Debian
```

> 本项目一律用 `py -3 -m` 调用（Windows）/ `python3 -m`（macOS / Linux），
> **不需要把 Scripts 目录加进 PATH，也不需要知道它在哪**。
> 装了多个 Python 时先 `py -0p` 看全部版本 —— `py -3` 挑的是**版本最高**的那个，
> 未必是你装包的那个；必要时指定版本，例如 `py -3.12 -m genshen_skins list`。



---

## 路线 B：不装 pip 包，按环境手动装

环境受限（不能 pip、没有 Python）时走这条。**先读 `catalog.json` 找到目标那套的
`repo`、`paths`、`caps`** —— 它记录的是从各仓库实测出来的真实路径与能力，
不要凭猜测拼 URL。

`catalog.json` 关键字段：

```jsonc
{
  "id": "furina", "repo": "Genshen-Furina-Skin", "char": "芙宁娜",
  "url": "https://github.com/WPH666-py/Genshen-Furina-Skin",
  "raw": "https://raw.githubusercontent.com/WPH666-py/Genshen-Furina-Skin/main",
  "caps": { "dsh": true, "vscode": true, "desktop": true, "deepking": true },
  "paths": {
    "dsh_client":  "dsh-plugin/client-standalone.js",  // DSH 客户端（素材已内嵌 base64）
    "dsh_host":    "dsh-plugin/host.js",               // 可选：全画质原图路由
    "vsix":        "vscode-extension/genshen-furina-skin-1.0.0.vsix",
    "desktop_ps1": "desktop/芙宁娜皮肤.ps1",
    "deepking_css":"src/client/deepking-skin.module.css"
  },
  "wallpapers": ["dsh-plugin/素材/芙宁娜-web.jpg", "..."],
  "ext": { "id": "wp666.genshen-furina-skin", "show": "furinaSkin.show" }
}
```

### B1. DeepSeek Harness（动态 Cordis 插件）

你能调用 `cordis_define` / `cordis_run` 就属于这种环境。

1. 下载该套皮肤的 `paths.dsh_client`（URL = `raw` + `/` + 路径）。文件较大
   （芙宁娜约 600 KB、丝柯克约 190 KB），**必须完整读取**，素材是内嵌 base64。
2. `cordis_define`：`plugin.kind = "new"`，`idPrefix` 取 3–6 位小写字母
   （超过 6 个字母的截断：`furina` `skirk` `keqing` `citlal` `columb` `sandron` …），
   `name` / `purpose` 按该套皮肤填，`code.client` = 上一步的完整源码，
   `code.host` 先不填（零配置模式）。
3. `cordis_run`（`mode = "run"`）。返回 `awaiting-approval` 就告诉用户在授权卡片上允许；
   **不要**等待或重试。
4. 告诉用户：页面右下角出现皮肤挂件，点击释放元素爆发（中文语音 + 特效），
   右键菜单含「切换壁纸」「一键卸载」。

若主工具可用，`py -3 -m genshen_skins dsh <id>` 会一次做完并写出 `DEFINE.md` 操作单。

> DSH 动态插件是**进程内**的，DSH 重启后需要重新 define + run。

### B2. VSCode / Trae / CodeX / Cursor / Windsurf / VSCodium（VSIX 扩展）

1. 下载 `paths.vsix` 到本地临时目录（仓库里已附打包好的 `.vsix`）。
2. 安装（`<cli>` 换成对应编辑器命令：`code` / `trae` / `cursor` / `windsurf` / `codium`）：
   ```bash
   code --install-extension "<vsix 完整路径>" --force
   ```
3. 没有 CLI 时：把 VSIX 当 zip 解压，把其中的 `extension/` 目录放到
   `%USERPROFILE%\.vscode\extensions\<ext.id>\`（Trae 用 `.trae\extensions`、
   Cursor 用 `.cursor\extensions`、Windsurf 用 `.windsurf\extensions`），
   并提示用户重启编辑器。
4. 告知用户：命令面板（Ctrl+Shift+P）运行扩展显示命令（`ext.show`）；
   皮肤右键菜单含「切换壁纸」「一键卸载」。

### B3. PyCharm / IntelliJ / WebStorm 等 JetBrains

JetBrains 不支持 VSIX，走**背景图**：

1. 下载该套的 `wallpapers`（`-web.jpg` 是优化过的网页图，直接当背景图足够）。
2. 让用户在 `Settings → Appearance & Behavior → Background Image` 里选一张。
3. 主工具可用时 `py -3 -m genshen_skins export <id> --out <目录>` 会按屏幕分辨率生成整屏壁纸
   （默认 `blur`：立绘完整 + 两侧模糊填充，无黑边）。

### B4. claude-code / kimi-code / CodeX CLI / 任意 Windows 桌面（桌宠）

桌宠是**透明置顶悬浮窗**，盖在所有窗口之上，因此覆盖所有编辑器
（PyCharm、claude-code、kimi-code、CodeX、Harness 都能被盖住）。

1. 下载该套仓库 `desktop/` 目录下的全部文件到本地（**保留 `素材/` 子目录结构**）。
2. Windows 后台启动：
   ```
   start "" powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "<目录>\<desktop_ps1 文件名>"
   ```
   或双击同目录的 `启动-*.bat`。
3. 告知用户：右下角出现悬浮皮肤，左键点击释放大招（语音 + 动画），可拖动；
   右键菜单含「切换壁纸」「开机自启」「一键卸载」。

> `caps.desktop` 为 `false` 的皮肤（目前只有刻晴）仓库里没有桌宠脚本。
> 主工具可用时 `py -3 -m genshen_skins pet <id>` 会用**内置通用桌宠**（读 `pet.json`）补上，效果对等。

### B5. DeepKing

下载 `paths.skin_json` + `paths.deepking_css` + 一张立绘，即 DeepKing 皮肤规范包
（配色变量 + 立绘）。主工具可用时 `py -3 -m genshen_skins deepking <id>` 会导出到本地目录。

---

## 全部安装

```bash
py -3 -m genshen_skins sync --all                      # 克隆 30 个仓库到 ~/.genshen-skins
py -3 -m genshen_skins vendor --out D:\GenshenAll      # 把 30 个仓库全部落地到指定目录
```

30 套逐套跑 `install` 会反复改系统壁纸，通常没必要；「都装上」一般指克隆 + 装扩展。

---

## 约定与失败处理

- **只读原则**：本仓库不含素材，安装时从各皮肤仓库按需拉取，不改动用户已有文件。
  生成物都在 `~/.genshen-skins/`（`GENSHEN_HOME` 可覆盖），不写进用户项目目录。
- **网络**：`raw.githubusercontent.com` 国内经常不通。`genshen-skin` 会自动依次尝试
  直连 → jsDelivr → ghfast → gitmirror → gh-proxy，第一个成功的会被记住。
  你手动下载时也可以换这些前缀，例如：
  `https://cdn.jsdelivr.net/gh/WPH666-py/Genshen-Furina-Skin@main/dsh-plugin/client-standalone.js`
- **代理**：桌面代理软件（Clash 等）通常只设 Windows 系统代理 —— git 能读、pip 读不到。
  主工具会把探测到的代理显式传给 git/pip；`GENSHEN_NO_PROXY=1` 关闭，
  `GENSHEN_PROXY=http://host:port` 指定。
- **base64 素材不得增删改**：`data:image/...;base64,` / `data:audio/...;base64,`
  之后的长串**不要换行、不要截断、不要"整理格式"**。
- **Windows 控制台中文乱码**：先 `chcp 65001`；主工具内置 UTF-8 兜底。
- **桌宠启动后立刻消失**：宿主（AI Agent 的一次命令执行、部分 IDE 终端）会给子进程建
  Job 对象并在结束时回收整棵进程树。主工具通过 `explorer.exe` 打开 `.bat` 启动以脱离它；
  手动启动时用上面的 `start ""` 形式。
- **桌宠看不到**：先 `py -3 -m genshen_skins pet <角色>` 看状态；内置通用桌宠有"兜底夹取"，
  会把窗口夹回主屏可见区域。
- **非 Windows 环境**：桌宠仅支持 Windows；DSH 插件、VSCode 扩展、壁纸合成与设置
  （macOS 走 AppleScript，Linux 走 gsettings/xfconf/feh/nitrogen）跨平台可用。
- **卸载**：`py -3 -m genshen_skins uninstall <id>`（清扩展 + 桌宠 + 自启 + 本地副本）；
  DSH 侧用皮肤右键菜单「一键卸载」或 `cordis_undefine <pluginId>`。

## 素材版权

立绘、壁纸、语音等素材版权归 **米哈游（miHoYo / HoYoverse）**，语音台词与音频来自原神 BWIKI。
本集合的**代码**是 MIT，但素材**不在** MIT 授权范围内，仅供个人学习与娱乐，
**不得商用**。用户问及商用时要如实说明。
