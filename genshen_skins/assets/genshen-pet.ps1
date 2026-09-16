# ============================================================
# genshen-pet.ps1 —— 原神皮肤「通用桌宠」（Windows PowerShell + WPF）
# ------------------------------------------------------------
# 由 genshen-skin (pip 包 genshen-desktop-skin) 自动部署。
# 与各皮肤仓库自带的定制桌宠功能对等：透明置顶、可拖动、点击释放大招
# （语音 + 光效）、右键菜单切换壁纸 / 收起 / 开机自启 / 一键卸载。
#
# 该脚本读取同目录的 pet.json（由安装器生成），因此对任意皮肤通用：
#   { id, char, name, accent, wallpapers[], voice, repo }
#
# 直接运行： powershell -NoProfile -STA -ExecutionPolicy Bypass -File genshen-pet.ps1
# ============================================================
param(
  [switch]$NoAutostartCheck
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ---------- 关于 DPI ----------
# 这里**故意不声明** DPI 感知，与 28 套皮肤仓库自带的桌宠脚本保持一致：
# 不声明时窗口尺寸按"逻辑像素"计算，在 150%/200% 缩放的显示器上会跟着放大，
# 视觉比例与那些定制桌宠完全一致。若声明感知会更清晰，但同一台机器上通用版
# 会比定制版小一半，反而不统一。窗口位置另有"兜底夹取"防止跑到屏幕外。

$root = $PSScriptRoot
$cfgPath = Join-Path $root 'pet.json'
if (-not (Test-Path $cfgPath)) {
  [System.Windows.MessageBox]::Show("找不到 pet.json，请用 genshen-skin pet <角色> 重新部署。", "原神桌宠") | Out-Null
  exit 1
}
$cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json

# 把自己的 PID 写给主程序（genshen-skin pet --stop / running 靠它判断）。
# 由脚本自己写才准：Windows 上用 DETACHED_PROCESS 启动时，
# CreateProcess 返回的 PID 并不是最终这个拥有窗口的进程。
try { Set-Content -LiteralPath (Join-Path $root '.pid') -Value $PID -Encoding ASCII } catch { }

$script:char      = [string]$cfg.char
$script:skinName  = [string]$cfg.name
$script:repo      = [string]$cfg.repo
$script:accentHex = if ($cfg.accent) { [string]$cfg.accent } else { '#7a7f8c' }

# ---------- 壁纸 / 语音 ----------
$script:wallFiles = @()
foreach ($w in @($cfg.wallpapers)) {
  $p = Join-Path $root ([string]$w)
  if (Test-Path -LiteralPath $p) { $script:wallFiles += $p }
}
if ($script:wallFiles.Count -eq 0) {
  $script:wallFiles = @(Get-ChildItem -LiteralPath $root -Filter *.jpg -ErrorAction SilentlyContinue |
                        Select-Object -ExpandProperty FullName)
}
$script:voiceFile = $null
if ($cfg.voice) {
  $vp = Join-Path $root ([string]$cfg.voice)
  if (Test-Path -LiteralPath $vp) { $script:voiceFile = $vp }
}
$script:wallIndex = 0
$script:CARD_W = 300
$script:CARD_H = 420
$script:runName = 'GenshenSkin_' + [string]$cfg.id

# ---------- 颜色 ----------
function Convert-HexToColor([string]$hex) {
  $h = $hex.TrimStart('#')
  if ($h.Length -eq 3) { $h = "$($h[0])$($h[0])$($h[1])$($h[1])$($h[2])$($h[2])" }
  if ($h.Length -ne 6) { $h = '7a7f8c' }
  return [System.Windows.Media.Color]::FromArgb(
    255,
    [Convert]::ToByte($h.Substring(0,2),16),
    [Convert]::ToByte($h.Substring(2,2),16),
    [Convert]::ToByte($h.Substring(4,2),16))
}
$script:accent = Convert-HexToColor $script:accentHex
function Accent-Brush([double]$opacity = 1.0) {
  $b = New-Object System.Windows.Media.SolidColorBrush($script:accent)
  $b.Opacity = $opacity
  return $b
}

# ---------- 声音 ----------
function Play-Voice {
  if (-not $script:voiceFile) { return }
  try {
    if ($script:voiceFile.ToLower().EndsWith('.wav')) {
      $sp = New-Object System.Media.SoundPlayer($script:voiceFile)
      $sp.Play()
    } else {
      $mp = New-Object System.Windows.Media.MediaPlayer
      $mp.Open((New-Object System.Uri($script:voiceFile)))
      $mp.Volume = 0.9
      $script:player = $mp   # 保活，否则会被 GC 掉导致没声音
      Start-Sleep -Milliseconds 120
      $mp.Play()
    }
  } catch { }
}

# ============================================================
# 主窗口
# ============================================================
$win = New-Object System.Windows.Window
$win.WindowStyle = [System.Windows.WindowStyle]::None
$win.AllowsTransparency = $true
$win.Background = [System.Windows.Media.Brushes]::Transparent
$win.Topmost = $true
$win.ShowInTaskbar = $false
$win.ResizeMode = [System.Windows.ResizeMode]::NoResize
$win.Width = $script:CARD_W
$win.Height = $script:CARD_H

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$win.Left = [Math]::Max(20, $screen.Right - $script:CARD_W - 60)
$win.Top  = [Math]::Max(20, $screen.Bottom - $script:CARD_H - 40)

# 兜底夹取：万一坐标体系仍与真实桌面不一致（多屏 / 混合缩放 / 远程桌面），
# 保证窗口至少完整落在主屏可见区域内，绝不跑到屏幕外面去。
try {
  $virt = [System.Windows.Forms.SystemInformation]::VirtualScreen
  if ($win.Left + $script:CARD_W -gt $virt.Right) {
    $win.Left = [Math]::Max(0, $virt.Right - $script:CARD_W - 20)
  }
  if ($win.Top + $script:CARD_H -gt $virt.Bottom) {
    $win.Top = [Math]::Max(0, $virt.Bottom - $script:CARD_H - 20)
  }
  if ($win.Left -lt $virt.Left) { $win.Left = $virt.Left + 20 }
  if ($win.Top  -lt $virt.Top)  { $win.Top  = $virt.Top + 20 }
} catch { }

$rootGrid = New-Object System.Windows.Controls.Grid
$win.Content = $rootGrid

# —— 光晕背景（点击时爆发）——
$glow = New-Object System.Windows.Controls.Border
$glow.CornerRadius = New-Object System.Windows.CornerRadius(18)
$glow.Background = Accent-Brush 0.0
$rootGrid.Children.Add($glow) | Out-Null

$stack = New-Object System.Windows.Controls.StackPanel
$rootGrid.Children.Add($stack) | Out-Null

# —— 立绘 ——
$img = New-Object System.Windows.Controls.Image
$img.Stretch = [System.Windows.Media.Stretch]::Uniform
$img.Height = $script:CARD_H - 74
$img.Cursor = [System.Windows.Input.Cursors]::Hand
if ($script:wallFiles.Count -gt 0) {
  $bi = New-Object System.Windows.Media.Imaging.BitmapImage
  $bi.BeginInit()
  $bi.UriSource = New-Object System.Uri($script:wallFiles[0])
  $bi.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
  $bi.EndInit()
  $img.Source = $bi
}
$stack.Children.Add($img) | Out-Null

# —— 技能名 / 台词条 ——
$bar = New-Object System.Windows.Controls.Border
$bar.CornerRadius = New-Object System.Windows.CornerRadius(10)
$bar.Margin = New-Object System.Windows.Thickness(8, 6, 8, 6)
$bar.Padding = New-Object System.Windows.Thickness(10, 6, 10, 6)
$bar.Background = New-Object System.Windows.Media.SolidColorBrush(
  [System.Windows.Media.Color]::FromArgb(190, 14, 16, 24))
$barText = New-Object System.Windows.Controls.TextBlock
$barText.Text = "$script:char · 点击释放元素爆发"
$barText.Foreground = New-Object System.Windows.Media.SolidColorBrush(
  [System.Windows.Media.Color]::FromArgb(255, 235, 238, 245))
$barText.FontSize = 12
$barText.TextAlignment = [System.Windows.TextAlignment]::Center
$barText.TextTrimming = [System.Windows.TextTrimming]::CharacterEllipsis
$bar.Child = $barText
$stack.Children.Add($bar) | Out-Null

# —— 收起胶囊 ——
$pill = New-Object System.Windows.Controls.Border
$pill.CornerRadius = New-Object System.Windows.CornerRadius(16)
$pill.Padding = New-Object System.Windows.Thickness(14, 6, 14, 6)
$pill.Background = New-Object System.Windows.Media.SolidColorBrush(
  [System.Windows.Media.Color]::FromArgb(215, 16, 18, 28))
$pill.BorderThickness = New-Object System.Windows.Thickness(1)
$pill.BorderBrush = Accent-Brush 0.75
$pill.Visibility = [System.Windows.Visibility]::Collapsed
$pill.Cursor = [System.Windows.Input.Cursors]::Hand
$pillText = New-Object System.Windows.Controls.TextBlock
$pillText.Text = "$script:char ✦"
$pillText.Foreground = Accent-Brush 1.0
$pillText.FontSize = 13
$pill.Child = $pillText
$rootGrid.Children.Add($pill) | Out-Null
$pill.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Center
$pill.VerticalAlignment = [System.Windows.VerticalAlignment]::Top

# ============================================================
# 大招特效
# ============================================================
function New-DoubleAnim([double]$from, [double]$to, [int]$ms, [bool]$autoReverse) {
  $a = New-Object System.Windows.Media.Animation.DoubleAnimation
  $a.From = $from; $a.To = $to
  $a.Duration = New-Object System.Windows.Duration([TimeSpan]::FromMilliseconds($ms))
  $a.AutoReverse = $autoReverse
  return $a
}

function Invoke-Burst {
  Play-Voice
  try {
    $glow.BeginAnimation([System.Windows.UIElement]::OpacityProperty,
      (New-DoubleAnim 1.0 0.0 900 $false))
    $scale = New-Object System.Windows.Media.ScaleTransform(1.0, 1.0)
    $img.RenderTransformOrigin = New-Object System.Windows.Point(0.5, 0.5)
    $img.RenderTransform = $scale
    $sx = New-DoubleAnim 1.0 1.06 260 $true
    $scale.BeginAnimation([System.Windows.Media.ScaleTransform]::ScaleXProperty, $sx)
    $scale.BeginAnimation([System.Windows.Media.ScaleTransform]::ScaleYProperty, $sx)
    $barText.Text = '元素爆发！'
    # 计时器存到 $script: 作用域：函数返回后局部变量就没了，
    # 而 Tick 回调是之后才触发的（回调里取局部的 $t 会失败）。
    $t = New-Object System.Windows.Threading.DispatcherTimer
    $t.Interval = [TimeSpan]::FromMilliseconds(1600)
    $script:burstTimer = $t
    $t.Add_Tick({
      $barText.Text = "$script:char · 点击释放元素爆发"
      if ($script:burstTimer) { $script:burstTimer.Stop() }
    })
    $t.Start()
  } catch { }
}

# ============================================================
# 交互
# ============================================================
$script:dragging = $false
$script:dragStart = $null

$onDown = {
  param($s, $e)
  $script:dragging = $false
  $script:dragStart = $e.GetPosition($win)
  $win.CaptureMouse() | Out-Null
}
$onMove = {
  param($s, $e)
  if ($null -eq $script:dragStart) { return }
  $p = $e.GetPosition($win)
  if ([Math]::Abs($p.X - $script:dragStart.X) -gt 4 -or
      [Math]::Abs($p.Y - $script:dragStart.Y) -gt 4) {
    $script:dragging = $true
    $win.ReleaseMouseCapture()
    try { $win.DragMove() } catch { }
    $script:dragStart = $null
  }
}
$onUp = {
  param($s, $e)
  if ($null -ne $script:dragStart) {
    $win.ReleaseMouseCapture() | Out-Null
    $script:dragStart = $null
    if (-not $script:dragging) { Invoke-Burst }
  }
}

foreach ($el in @($img, $bar)) {
  $el.Add_MouseLeftButtonDown($onDown)
  $el.Add_MouseMove($onMove)
  $el.Add_MouseLeftButtonUp($onUp)
}
$pill.Add_MouseLeftButtonDown({
  $pill.Visibility = [System.Windows.Visibility]::Collapsed
  $img.Visibility = [System.Windows.Visibility]::Visible
  $bar.Visibility = [System.Windows.Visibility]::Visible
  $win.Width = $script:CARD_W
  $win.Height = $script:CARD_H
})
$pill.Add_MouseMove({
  param($s, $e)
  if ($e.LeftButton -eq [System.Windows.Input.MouseButtonState]::Pressed) {
    try { $win.DragMove() } catch { }
  }
})

# ---------- 右键菜单 ----------
function Set-Wallpaper([int]$i) {
  if ($script:wallFiles.Count -eq 0) { return }
  $script:wallIndex = (($i % $script:wallFiles.Count) + $script:wallFiles.Count) % $script:wallFiles.Count
  $bi = New-Object System.Windows.Media.Imaging.BitmapImage
  $bi.BeginInit()
  $bi.UriSource = New-Object System.Uri($script:wallFiles[$script:wallIndex])
  $bi.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
  $bi.EndInit()
  $img.Source = $bi
  $barText.Text = "壁纸 · 其$([char](0x4E00 + $script:wallIndex))"
}

$menu = New-Object System.Windows.Controls.ContextMenu
function Add-MenuItem([string]$header, [scriptblock]$action) {
  $mi = New-Object System.Windows.Controls.MenuItem
  $mi.Header = $header
  $mi.Add_Click($action)
  $menu.Items.Add($mi) | Out-Null
  return $mi
}

Add-MenuItem '释放元素爆发' { Invoke-Burst } | Out-Null
$wallMenu = New-Object System.Windows.Controls.MenuItem
$wallMenu.Header = '切换壁纸'
for ($i = 0; $i -lt $script:wallFiles.Count; $i++) {
  $idx = $i
  $sub = New-Object System.Windows.Controls.MenuItem
  $sub.Header = "壁纸 · 其$([char](0x4E00 + $idx))"
  $sub.Add_Click({ Set-Wallpaper $idx }.GetNewClosure())
  $wallMenu.Items.Add($sub) | Out-Null
}
$rn = New-Object System.Windows.Controls.MenuItem
$rn.Header = '随机换一张'
$rn.Add_Click({ Set-Wallpaper (Get-Random -Minimum 0 -Maximum ([Math]::Max(1, $script:wallFiles.Count))) }) | Out-Null
$wallMenu.Items.Add($rn) | Out-Null
$menu.Items.Add($wallMenu) | Out-Null

Add-MenuItem '收起' {
  $img.Visibility = [System.Windows.Visibility]::Collapsed
  $bar.Visibility = [System.Windows.Visibility]::Collapsed
  $pill.Visibility = [System.Windows.Visibility]::Visible
  $win.Width = 150
  $win.Height = 46
} | Out-Null

$auto = New-Object System.Windows.Controls.MenuItem
$auto.Header = '开机自启'
$auto.IsCheckable = $true
try {
  $auto.IsChecked = [bool](Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $script:runName -ErrorAction SilentlyContinue)
} catch { }
$auto.Add_Click({
  $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
  if ($auto.IsChecked) {
    $cmd = 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + (Join-Path $root 'genshen-pet.ps1') + '"'
    Set-ItemProperty -Path $key -Name $script:runName -Value $cmd -Type String
  } else {
    Remove-ItemProperty -Path $key -Name $script:runName -ErrorAction SilentlyContinue
  }
}) | Out-Null
$menu.Items.Add($auto) | Out-Null
$menu.Items.Add((New-Object System.Windows.Controls.Separator)) | Out-Null

Add-MenuItem '一键卸载' {
  $ok = [System.Windows.MessageBox]::Show(
    "确定卸载 $script:char 桌宠？`n将移除开机自启并删除本地桌宠文件。",
    '原神桌宠', 'YesNo', 'Question')
  if ($ok -ne 'Yes') { return }
  try { Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $script:runName -ErrorAction SilentlyContinue } catch { }
  # 脚本自己就在被删的目录里，不能当场删 —— 派生一个脱离的 cmd，
  # 先 ping 两次（约 2 秒，不需要控制台）等本进程退出，再删目录。
  $target = $root
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/c', "ping -n 3 127.0.0.1 >nul & rmdir /s /q `"$target`"" `
    -WindowStyle Hidden
  $win.Close()
} | Out-Null
Add-MenuItem '退出' { $win.Close() } | Out-Null

$img.ContextMenu = $menu
$bar.ContextMenu = $menu
$pill.ContextMenu = $menu
$glow.ContextMenu = $menu

# 透明区域也要能右键：整个窗口都挂上菜单
$win.Add_MouseRightButtonUp({ $menu.IsOpen = $true })

$win.ShowDialog() | Out-Null
