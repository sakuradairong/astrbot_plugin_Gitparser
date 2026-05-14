# astrbot_plugin_Gitparser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AstrBot plugin that auto-detects GitHub URLs in messages and replies with repo/release summary as plain text.

**Architecture:** Single-file plugin (`main.py`) using regex for URL matching and aiohttp for GitHub REST API calls. Configuration via `_conf_schema.json` (optional token). Output formatted plain text.

**Tech Stack:** Python 3.10+, aiohttp, AstrBot Star API

---

## File Map

| File | Purpose |
|------|---------|
| `metadata.yaml` | Plugin metadata (name, desc, version, author) |
| `_conf_schema.json` | Config schema: `github_token` (optional string) |
| `requirements.txt` | `aiohttp` dependency |
| `main.py` | All plugin logic in one class |

---

### Task 1: Plugin Metadata

**Files:**
- Create: `metadata.yaml`

- [ ] **Step 1: Write metadata.yaml**

```yaml
name: Gitparser
desc: 自动解析 GitHub 仓库和 Release 链接并展示摘要信息。
version: 1.0.0
author: chena
```

- [ ] **Step 2: Commit**

```bash
git add metadata.yaml
git commit -m "feat: add plugin metadata"
```

---

### Task 2: Plugin Configuration Schema

**Files:**
- Create: `_conf_schema.json`

- [ ] **Step 1: Write _conf_schema.json**

```json
{
  "github_token": {
    "description": "GitHub Personal Access Token（可选，用于突破 API 速率限制）",
    "type": "string",
    "hint": "不填则为无认证模式（60次/小时），填写 Token 后提升到 5000次/小时",
    "default": ""
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add _conf_schema.json
git commit -m "feat: add config schema with optional github_token"
```

---

### Task 3: Dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Write requirements.txt**

```
aiohttp>=3.9.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt
git commit -m "feat: add aiohttp dependency"
```

---

### Task 4: Main Plugin Logic

**Files:**
- Create: `main.py`

- [ ] **Step 1: Write main.py**

```python
import re
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, star
from astrbot.api import logger, AstrBotConfig

GITHUB_API_BASE = "https://api.github.com"

# Regex: match github.com/{owner}/{repo} with optional sub-path
_REPO_PATTERN = re.compile(
    r'github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)'
    r'(?:\.git)?'
    r'(?:\s|$|[^\w./-])'
)

_RELEASE_TAG_PATTERN = re.compile(
    r'github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/releases/tag/([^\s/]+)'
)

_RELEASES_PAGE_PATTERN = re.compile(
    r'github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/releases'
    r'(?:\s|$|[^\w./-])'
)


def _find_first_url(text: str, pattern: re.Pattern) -> re.Match | None:
    for m in pattern.finditer(text):
        return m
    return None


@star
class GitparserPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def parse_github_link(self, event: AstrMessageEvent):
        text = event.message_str

        # 1) Release tag URL: github.com/owner/repo/releases/tag/xxx
        m = _find_first_url(text, _RELEASE_TAG_PATTERN)
        if m:
            yield await self._handle_release_by_tag(event, m.group(1), m.group(2), m.group(3))
            return

        # 2) Releases page: github.com/owner/repo/releases
        m = _find_first_url(text, _RELEASES_PAGE_PATTERN)
        if m:
            yield await self._handle_latest_release(event, m.group(1), m.group(2))
            return

        # 3) Repo URL: github.com/owner/repo
        m = _find_first_url(text, _REPO_PATTERN)
        if m:
            owner, repo = m.group(1), m.group(2)
            # if it happens to be a releases page (overlap with pattern 2's partial match),
            # skip because releases page was already handled above.
            # The _REPO_PATTERN might also match releases/... so check:
            remaining = text[m.end():].strip()
            if remaining.startswith('releases/'):
                return
            yield await self._handle_repo(event, owner, repo)

    async def _fetch_api(self, path: str) -> dict | None:
        headers = {"Accept": "application/vnd.github+json"}
        token = self.config.get("github_token", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        url = f"{GITHUB_API_BASE}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 404:
                        return None
                    if resp.status == 429:
                        logger.warning(f"GitHub API rate limited: {path}")
                        return {"error": "rate_limited"}
                    if resp.status != 200:
                        logger.warning(f"GitHub API error {resp.status}: {path}")
                        return None
                    return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {path}: {e}")
            return None

    async def _handle_repo(self, event: AstrMessageEvent, owner: str, repo: str):
        data = await self._fetch_api(f"/repos/{owner}/{repo}")
        if data is None:
            return
        if isinstance(data, dict) and data.get("error") == "rate_limited":
            yield event.plain_result("GitHub API 限流，请稍后再试")
            return

        full_name = data.get("full_name", f"{owner}/{repo}")
        description = data.get("description") or "(无描述)"
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        language = data.get("language") or "未知"
        updated_at = data.get("updated_at", "")[:10]
        license_info = data.get("license")
        license_name = license_info["spdx_id"] if license_info and isinstance(license_info, dict) else "无"

        lines = [
            f"\U0001f4e6 {full_name}",
            f"{description}",
            f"\u2b50 Stars: {stars}  |  \U0001f354 Forks: {forks}  |  \U0001f524 语言: {language}",
            f"\U0001f4c5 最后更新: {updated_at}  |  \U0001f513 {license_name}",
        ]
        yield event.plain_result("\n".join(lines))

    async def _handle_latest_release(self, event: AstrMessageEvent, owner: str, repo: str):
        data = await self._fetch_api(f"/repos/{owner}/{repo}/releases/latest")
        if data is None:
            return
        if isinstance(data, dict) and data.get("error") == "rate_limited":
            yield event.plain_result("GitHub API 限流，请稍后再试")
            return

        tag_name = data.get("tag_name", "unknown")
        name = data.get("name") or tag_name
        published_at = data.get("published_at", "")[:10]
        zip_url = data.get("zipball_url", "")

        lines = [
            f"\U0001f680 {owner}/{repo} - {tag_name}",
            f"\U0001f4dd {name}",
            f"\U0001f4c5 发布于: {published_at}",
            f"\U0001f4e6 下载: {zip_url}",
        ]
        yield event.plain_result("\n".join(lines))

    async def _handle_release_by_tag(self, event: AstrMessageEvent, owner: str, repo: str, tag: str):
        data = await self._fetch_api(f"/repos/{owner}/{repo}/releases/tags/{tag}")
        if data is None:
            return
        if isinstance(data, dict) and data.get("error") == "rate_limited":
            yield event.plain_result("GitHub API 限流，请稍后再试")
            return

        tag_name = data.get("tag_name", tag)
        name = data.get("name") or tag_name
        published_at = data.get("published_at", "")[:10]
        zip_url = data.get("zipball_url", "")

        lines = [
            f"\U0001f680 {owner}/{repo} - {tag_name}",
            f"\U0001f4dd {name}",
            f"\U0001f4c5 发布于: {published_at}",
            f"\U0001f4e6 下载: {zip_url}",
        ]
        yield event.plain_result("\n".join(lines))
```

- [ ] **Step 2: Commit**

```bash
git add main.py
git commit -m "feat: implement GitHub URL parsing and summary"
```

---

### Task 5: Final Verification

- [ ] **Step 1: Review file structure**

```bash
Get-ChildItem -Recurse -File | Select-Object -ExpandProperty FullName
```

- [ ] **Step 2: Commit design doc**

```bash
git add docs/
git commit -m "docs: add design spec and implementation plan"
```

