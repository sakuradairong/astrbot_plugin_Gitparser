# Gitparser

AstrBot 插件，自动检测消息中的 GitHub 链接，解析仓库和 Release 信息并回复摘要。

## 功能

- **中文仓库介绍** — 使用当前会话配置的大模型，根据仓库描述、语言和 Topics 生成一句简短中文介绍
- **仓库解析** — 发送 GitHub 仓库链接，回复仓库名称、中英文描述、Stars、Forks、语言、最近更新时间、License
- **Release 解析** — 发送 Release 链接或版本链接，回复版本号、名称、发布时间、下载地址

## 效果示例

```
📦 owner/repo
🇨🇳 这是一个使用 Python 开发的轻量级 GitHub 链接解析工具。
📝 A lightweight GitHub link parser
🔗 https://github.com/owner/repo
⭐ 1,234  🍴 56  👁 1,234  ❗ 3
🔤 Python  📅 Updated 2026-05-14  📆 Created 2026-01-01
🔓 MIT
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

仓库原始描述已经是中文时，插件会直接将其作为中文介绍，避免额外调用模型。英文描述或无描述仓库会使用当前会话选择的聊天模型生成中文介绍；如果没有可用模型或模型调用失败，则自动返回基于语言和 Topics 生成的中文概述，不影响仓库信息解析。

## 依赖

- `aiohttp >= 3.9.0, < 4.0.0`

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 调试方式：在 AstrBot 项目 data/plugins/ 下克隆此仓库，启动 AstrBot 后自动加载
```

插件遵循 [AstrBot 插件开发规范](https://docs.astrbot.app/dev/star/plugin-new.html)。

## 更新记录

- `1.2.1`：适配当前 AstrBot 插件自动注册机制，修复加载时无法导入 `star` 的问题。
- `1.2.0`：新增中文仓库介绍。
