# INSTALL.md — 分环境安装说明与排错

29 套皮肤，同一份素材，装到不同环境。先看「最快路径」，遇到问题再往下查。

---

## 0. 最快路径

```powershell
py -3 -m pip install genshen-desktop-skin
py -3 -m genshen_skins env                  # 确认识别到了什么
py -3 -m genshen_skins install <角色>       # 装（角色可用中文名 / 英文名 / 拼音 / 别名）
```

> **macOS / Linux 把 `py -3` 换成 `python3`**，其余完全一样。

`<角色>` 例子：`skirk` `furina` `雷神` `草神` `神里绫华` `keqing`。
不确定 id 就跑 `py -3 -m genshen_skins list`。



`install` 会**按本机情况自动取舍**：有 VSCode 就装扩展，屏幕有分辨率就按它合成壁纸，
Windows 就起桌宠；不支持的部分会明确跳过并说明，不会报错中断。

---

## 1. DeepSeek Harness（DSH 动态插件）

DSH 里皮肤是一个**动态 Cordis 插件**，素材 base64 内嵌，零配置。

**方式 A：让 DSH 里的 AI 自己装（最省事）**

```
请安装 https://github.com/WPH666-py/Genshen-Desktop-Skin 的芙宁娜皮肤
```

AI 会读 `AGENTS.md` 与 `catalog.json`，自己完成 define + run。

**方式 B：用命令行准备载荷**

```bash
py -3 -m genshen_skins dsh furina            # 下载 client.js，并打印操作单
py -3 -m genshen_skins dsh furina --with-host  # 另外准备全画质 host.js
```

产物在 `~/.genshen-skins/_dsh/<id>/`：`client.js`、可选 `host.js`、`DEFINE.md`（操作单）、
以及预览。把 `client.js` 全文喂给 `cordis_define` 的 `code.client`，再 `cordis_run`。

**全画质原图**：`host.js` 会把素材路由到本地 `素材/` 目录，`ASSET_DIR` 已被改成绝对路径，
一起 define 即可。

注意：
- 动态插件是**进程内**的，DSH 重启后需要重新 define + run。
- 各套皮肤的 `idPrefix`：`skirk` `furina` `keqing` `hutao` `kokomi` `ayaka` `lumine`
  `shenhe` `eula` `ganyu` `navia` `yelan` `ambor` `zibai` `nilou` `nahida` `nicole`
  `citlal` `yoimiy` `sucros` `barbar` `collei` `shogun` `linnea` `mualan` `columb`
  `sandron` `clorind` `escoff`（超过 6 个字母的自动截断，保证 3–6 位且互不重复）。
- 卸载：皮肤右键菜单「一键卸载」，或 `cordis_undefine <pluginId>`。

---

## 2. VSCode / Trae / CodeX / Cursor / Windsurf / VSCodium

```bash
py -3 -m genshen_skins ide --list            # 看检测到了哪些编辑器
py -3 -m genshen_skins ide furina            # 装到全部检测到的编辑器
py -3 -m genshen_skins ide furina --editor trae   # 只装到 Trae
py -3 -m genshen_skins ide furina --uninstall     # 卸载
```

装完在命令面板（`Ctrl+Shift+P`）运行扩展的显示命令（如「芙宁娜动态皮肤（原神）」→ 显示），
皮肤右键菜单含「切换壁纸」「一键卸载」。

**编辑器没有 CLI 时**：工具会把 VSIX 当 zip 解压到对应扩展目录
（VSCode `.vscode/extensions`、Trae `.trae/extensions`、Cursor `.cursor/extensions`、
Windsurf `.windsurf/extensions`、VSCodium `.vscode-oss/extensions`），
重启编辑器生效。

**手动装**：把仓库里的 `vscode-extension/*.vsix` 拖进编辑器，或

```bash
code --install-extension genshen-furina-skin-1.0.0.vsix --force
```

---

## 3. PyCharm / IntelliJ / WebStorm（JetBrains）

JetBrains 不支持 VSIX，走**背景图**：

```bash
py -3 -m genshen_skins export furina --out D:\skins
```

会按你的屏幕分辨率导出整屏壁纸（默认 `blur` 适配：立绘完整、两侧模糊填充、无黑边）。
然后 `Settings → Appearance & Behavior → Background Image` 选一张。

想要"壁纸铺满但立绘被裁切"的效果，加 `--fit cover`；想留白加 `--fit contain`。

---

## 4. claude-code / kimi-code / CodeX CLI / 任意 Windows 桌面（桌宠）

桌宠是**透明置顶悬浮窗**，盖在所有应用之上 —— 所以 PyCharm、claude-code、kimi-code、
CodeX、Harness 全都能被它覆盖，这也是"覆盖所有 IDE"实际起作用的那条路径。

```bash
py -3 -m genshen_skins pet furina                 # 启动
py -3 -m genshen_skins pet furina --stop          # 停止
py -3 -m genshen_skins pet furina --autostart     # 开机自启
py -3 -m genshen_skins pet furina --no-autostart  # 关闭自启
py -3 -m genshen_skins pet furina --uninstall     # 卸载（含自启与本地文件）
py -3 -m genshen_skins pet furina --generic       # 强制用内置通用桌宠
```

操作：左键点击释放元素爆发（中文语音 + 特效），拖动移动，右键菜单
「释放元素爆发 / 切换壁纸 / 收起 / 开机自启 / 一键卸载 / 退出」。

- 28 套皮肤用仓库自带的**定制桌宠**（各自的大招特效）。
- 刻晴仓库没有桌宠脚本，工具会用**内置通用桌宠**（`genshen_skins/assets/genshen-pet.ps1`
  + 自动生成的 `pet.json`），壁纸与语音同样来自刻晴仓库。
- 手动启动：给 AI 的指引是
  `start "" powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "<目录>\<xxx>皮肤.ps1"`，
  或双击同目录的 `.bat`。

---

## 5. DeepKing

```bash
py -3 -m genshen_skins deepking furina           # 导出到 ~/.genshen-skins/_deepking/furina
py -3 -m genshen_skins deepking furina --out D:\deepking\furina
```

导出内容：`skin.json`（主题色 / 标语）、`src/client/deepking-skin.module.css`（CSS 变量）、
一张立绘、以及汇总的 `genshen-skin.json`。

---

## 6. 全部落地到本地（离线收藏 / 自建镜像）

```bash
py -3 -m genshen_skins sync --all                  # 克隆 29 个仓库到 ~/.genshen-skins
py -3 -m genshen_skins vendor --out D:\GenshenAll  # 克隆到指定目录
python scripts/vendor_all.py --out D:\GenshenAll   # 等价脚本（带 .git 可 git pull 更新）
```

---

## 排错

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
- 连字符入口（`genshen-skin.py` / `genshen_skin.py`）包内仍然保留、也仍然可用，
  但文档统一只推 `genshen_skins`（下划线复数，正式包名）一种，少一层困惑。
- 三个名字别混：pip 发行名 `genshen-desktop-skin` / 模块名 `genshen_skins` / 命令名 `genshen-skin`。



### 装不上 pip 包 / 卡在 pypi.org

```powershell
py -3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple genshen-desktop-skin
py -3 -m pip install -i https://mirrors.ustc.edu.cn/pypi/simple genshen-desktop-skin
py -3 -m pip install -i https://mirrors.aliyun.com/pypi/simple genshen-desktop-skin
py -3 -m genshen_skins doctor        # 实测哪个源通
```



下载包体时如果报 `SSL: UNEXPECTED_EOF_WHILE_READING`，通常是桌面代理只设了
Windows 系统代理（pip 读不到）。换镜像即可，或给 pip 显式指定代理。

详见 [MIRRORS.md](MIRRORS.md)。

### 克隆皮肤仓库失败 / raw 下载超时

工具会自动在直连 → jsDelivr → ghfast → gitmirror → gh-proxy 之间回退；
全部失败还会退回下载源码包。手动克隆可以加加速前缀：

```bash
git clone https://ghfast.top/https://github.com/WPH666-py/Genshen-Furina-Skin.git
```

### git 能克隆但 pip 装不上

典型的"代理只设了系统代理"。工具会把探测到的代理显式传给 pip；
也可以手动 `set HTTPS_PROXY=http://127.0.0.1:7897`。

### Windows 控制台中文乱码

```bash
chcp 65001
```

工具内部已做 UTF-8 兜底；`scripts/sync_catalog.py` 等脚本同样。

### 桌宠启动了但立刻消失

宿主（AI Agent 的一次命令执行、部分 IDE 集成终端）会给子进程建 Job 对象并在结束时
回收整棵进程树。工具通过 `explorer.exe` 打开 `.bat` 来启动，从而脱离该进程树；
手动启动时用 `start "" powershell.exe ...` 也要注意这一点。

### 桌宠看不到 / 跑到屏幕外

先确认它在跑：`py -3 -m genshen_skins pet <角色>` 会打印状态；
再确认自启项：`py -3 -m genshen_skins pet <角色> --autostart`。
内置通用桌宠有"兜底夹取"，会把窗口夹回主屏可见区域；缩放显示器（150%/200%）上窗口会跟着放大，
这是为与定制桌宠保持一致。

### 壁纸被任务栏挡住 / 人物被裁掉

```bash
py -3 -m genshen_skins wallpaper furina 1 --fit blur      # 默认：完整 + 模糊填充（推荐）
py -3 -m genshen_skins wallpaper furina 1 --fit contain   # 完整 + 纯色留白
py -3 -m genshen_skins wallpaper furina 1 --fit cover     # 铺满 + 裁切
py -3 -m genshen_skins wallpaper furina 1 --size 2560x1440  # 指定分辨率
```

### 非 Windows 环境

桌宠仅支持 Windows。DSH 插件、VSCode 扩展、壁纸合成与设置（macOS 用 AppleScript、
Linux 走 gsettings/xfconf/feh/nitrogen）跨平台可用。

### 卸载

```bash
py -3 -m genshen_skins uninstall furina            # 扩展 + 桌宠 + 自启 + 本地副本
py -3 -m genshen_skins uninstall furina --keep-files  # 保留已下载的仓库文件
```

DSH 动态插件另外用右键菜单「一键卸载」或 `cordis_undefine <pluginId>`。

---

## 目录约定

| 路径 | 内容 |
|---|---|
| `~/.genshen-skins/<仓库名>/` | 克隆下来的皮肤仓库 |
| `~/.genshen-skins/_wallpapers/` | 合成的壁纸（按 `id-序号-分辨率.jpg` 命名） |
| `~/.genshen-skins/_pets/<仓库名>/` | 桌宠副本（含 `pet.json`、`genshen-launch.bat`、`.pid`） |
| `~/.genshen-skins/_dsh/<id>/` | DSH 载荷与 `DEFINE.md` |
| `~/.genshen-skins/_deepking/<id>/` | DeepKing 皮肤包导出 |

`GENSHEN_HOME` 可改根目录。所有生成物都在这里，不写进你的项目。
