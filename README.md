# Gitparser

AstrBot 插件，自动检测消息中的 GitHub 链接，解析仓库和 Release 信息并回复摘要。

## 功能

- **仓库解析** — 发送 GitHub 仓库链接，回复仓库名称、描述、Stars、Forks、语言、最近更新时间、License
- **Release 解析** — 发送 Release 链接或版本链接，回复版本号、名称、发布时间、下载地址

## 效果示例

```
📦 owner/repo
A cool project description
⭐ Stars: 1234  |  🍴 Forks: 56  |  🔤 语言: Python
📅 最后更新: 2026-05-14  |  🔓 MIT
```

```
🚀 owner/repo - v1.0.0
📝 First release
📅 发布于: 2026-05-14
📦 下载: https://api.github.com/repos/owner/repo/zipball/v1.0.0
```

## 安装

### 方式一：WebUI 插件市场

在 AstrBot WebUI 的插件市场中搜索 `Gitparser` 安装。

### 方式二：手动安装

```bash
cd AstrBot/data/plugins
git clone https://github.com/sakuradairong/astrbot_plugin_Gitparser
```

## 配置

在 WebUI 插件页配置：

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `github_token` | string | GitHub Personal Access Token（可选）。不填使用无认证模式（速率限制较低），填写后可大幅提升 API 速率限制 |

### 获取 Token

1. 访问 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. 创建 Token 时不需勾选任何权限（仅用于提升速率限制）
3. 将生成的 Token 填入插件配置

## 使用

无需指令，在任意对话中发送 GitHub 链接即可自动解析：

- `https://github.com/owner/repo` → 仓库摘要
- `https://github.com/owner/repo/releases` → 最新 Release
- `https://github.com/owner/repo/releases/tag/v1.0.0` → 指定版本 Release

支持的链接格式：
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `https://github.com/owner/repo/releases`
- `https://github.com/owner/repo/releases/tag/v1.0.0`

不支持的链接类型不会触发回复：Issue、PR、Commit、文件、Gist 等。

## 依赖

- `aiohttp >= 3.9.0, < 4.0.0`

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 调试方式：在 AstrBot 项目 data/plugins/ 下克隆此仓库，启动 AstrBot 后自动加载
```

插件遵循 [AstrBot 插件开发规范](https://docs.astrbot.app/dev/star/plugin-new.html)。
