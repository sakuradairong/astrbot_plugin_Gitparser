# astrbot_plugin_Gitparser 设计文档

## 概述

AstrBot 插件，自动检测消息中的 GitHub 链接，解析仓库和 Release 信息并以纯文本回复。

## 需求摘要

- **功能**: 仓库摘要卡片 + Release/下载信息
- **GitHub API Token**: 可选配置
- **输出格式**: 纯文本
- **触发方式**: 自动检测消息中的 GitHub URL

## 架构

```
消息 → @filter.event_message_type(ALL) → 正则匹配GH URL
→ 调用 GitHub REST API → 格式化纯文本 → 回复
```

## URL 解析规则

### 匹配的链接

| 类型 | 正则模式 | 行为 |
|------|----------|------|
| 仓库 | `github.com/{owner}/{repo}` | 调用 `/repos/{owner}/{repo}` |
| 仓库(.git) | `github.com/{owner}/{repo}.git` | 同上 |
| Release | `github.com/{owner}/{repo}/releases/tag/{tag}` | 调用 `/repos/{owner}/{repo}/releases/tags/{tag}` |
| Release(latest) | `github.com/{owner}/{repo}/releases` | 调用 `/repos/{owner}/{repo}/releases/latest` |

### 忽略的链接类型

- Issue/PR: `github.com/{owner}/{repo}/issues/{n}`, `/pull/{n}`
- Commit: `github.com/{owner}/{repo}/commit/{sha}`
- 文件: `github.com/{owner}/{repo}/blob/...`
- Gist: `gist.github.com/...`
- 其他（如 explore、marketplace 等）

## API 调用

| 类型 | API |
|------|-----|
| 仓库 | `GET /repos/{owner}/{repo}` |
| Release (latest) | `GET /repos/{owner}/{repo}/releases/latest` |
| Release (by tag) | `GET /repos/{owner}/{repo}/releases/tags/{tag}` |

Token 从配置读取，有则添加 `Authorization: Bearer` 头，无则不添加。

## 输出格式

### 仓库摘要
```
📦 {owner}/{repo}
{description}
⭐ Stars: {stars}  |  🍴 Forks: {forks}  |  🔤 语言: {language}
📅 最后更新: {updated_at}  |  🔓 {license}
```

### Release 信息
```
🚀 {owner}/{repo} - {tag_name}
📝 {name}
📅 发布于: {published_at}
📦 下载: {zip_url}
```

## 插件配置 (_conf_schema.json)

```json
{
  "github_token": {
    "type": "string",
    "description": "GitHub Personal Access Token（可选）",
    "hint": "填写 Token 可将 API 速率限制从 60次/小时提升到 5000次/小时",
    "default": ""
  }
}
```

## 文件结构

```
astrbot_plugin_Gitparser/
├── main.py
├── metadata.yaml
├── _conf_schema.json
├── requirements.txt
└── logo.png (可选)
```

## 依赖

- `aiohttp` - 异步 HTTP 请求，调用 GitHub API

## 错误处理

- API 404 → 静默，不回复
- API 限流(429) → 回复「GitHub API 限流，请稍后再试」
- 网络超时 → 静默
- 其他异常 → 记录日志，不回复

## 开发原则

- 使用 `aiohttp` 异步请求库，不使用 `requests`
- 使用 `astrbot.api.logger` 记录日志
- 配置文件持久化在 `data/config/` 下
