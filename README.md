# 物理复习提纲阅读器

把「复习提纲」和「教材 / 讲义 / 习题解答」放在同一个窗口里的离线 / 网页阅读器。

- 量子力学：教材 323 页、习题解答 436 页、19 份课件 218 页
- 热力学统计物理：教材 340 页（汪志诚第六版）、3 份课堂讲义 219 页
- 左侧提纲点卡片，右侧跳到对应教材/讲义页；支持书签、笔记、框选高亮、全局搜索、章节目录、阅读进度记忆

## 在线网页版

已上线（GitHub Pages）：

```
https://thunderauthur-source.github.io/physics-review-reader/
```

仓库：<https://github.com/thunderauthur-source/physics-review-reader>

网页版是纯静态文件，不需要后端。GitHub Pages 从仓库 `docs/` 目录发布；`发布/网页版/` 是同一份网页版的本地副本。

## 目录结构

```
程序/                     本机 Edge 阅读器（Windows）
  QMLauncher.exe
  resources/app/          界面、提纲、页面图、manifest
HTML/                     两份单文件可打印提纲
发布/
  安装版/                 单文件安装包与说明（exe 放在 Releases）
  网页版/                 静态网页版的本地副本
docs/                     GitHub Pages 发布目录（网页版）
构建/                     数据生成、自检、安装器源码
说明.txt                  本机版详细说明
```

## 本地使用

### 网页版

```bash
cd 发布/网页版
python -m http.server 8080 --bind 127.0.0.1
# 打开 http://127.0.0.1:8080/
```

也可以直接双击 `发布/网页版/index.html`，但 `file://` 下「导出当前页 PNG」会受 canvas 限制。

### Windows 安装版

下载地址（GitHub Releases）：

```
https://github.com/thunderauthur-source/physics-review-reader/releases/tag/v1.0
```

文件名 `PhysicsReader_v1.0_Installer.exe`，首次运行会让用户选择安装位置（默认 `D:\物理复习提纲阅读器`），不自动装进 C 盘。

## 构建

- `构建/自检.py`：检查页面图、manifest、提纲链接、搜索索引
- `构建/生成搜索索引.py`：修改提纲后重建搜索索引
- `构建/生成热统教材链接.py`：重建热统教材/讲义双链接
- `构建/安装器/Bootstrapper.cs`：单文件安装器源码

## 数据与版权

教材、课件、习题解答的版权归原作者与出版社所有。本仓库仅用于个人复习存档，不构成对这些资料的再授权；请勿商用或公开传播。如有侵权，请联系删除。

页面图经过 WebP 压缩（约 137 MB，1536 页）。
