import re
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig

GITHUB_API_BASE = "https://api.github.com"

_REPO_PATTERN = re.compile(
    r'(?<![a-zA-Z0-9.-])github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)'
    r'(?:\.git)?'
    r'(?:\s|$|[^\w./-])'
)

_RELEASE_TAG_PATTERN = re.compile(
    r'(?<![a-zA-Z0-9.-])github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/releases/tag/([^\s/]+)'
    r'(?:\s|$|[^\w./-])'
)

_RELEASES_PAGE_PATTERN = re.compile(
    r'(?<![a-zA-Z0-9.-])github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/releases'
    r'(?:\s|$|[^\w./-])'
)


def _find_first_url(text: str, pattern: re.Pattern) -> re.Match | None:
    return pattern.search(text)


class GitparserPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def parse_github_link(self, event: AstrMessageEvent):
        text = event.message_str

        m = _find_first_url(text, _RELEASE_TAG_PATTERN)
        if m:
            yield await self._handle_release_by_tag(event, m.group(1), m.group(2), m.group(3))
            return

        m = _find_first_url(text, _RELEASES_PAGE_PATTERN)
        if m:
            yield await self._handle_latest_release(event, m.group(1), m.group(2))
            return

        m = _find_first_url(text, _REPO_PATTERN)
        if m:
            owner, repo = m.group(1), m.group(2)
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
            f"\u2b50 Stars: {stars}  |  \U0001f374 Forks: {forks}  |  \U0001f524 语言: {language}",
            f"\U0001f4c5 最后更新: {updated_at}  |  \U0001f513 {license_name}",
        ]
        yield event.plain_result("\n".join(lines))

    def _build_release_message(self, owner: str, repo: str, data: dict, fallback_tag: str = "unknown") -> str:
        tag_name = data.get("tag_name", fallback_tag)
        name = data.get("name") or tag_name
        published_at = data.get("published_at", "")[:10]
        zip_url = data.get("zipball_url", "")

        lines = [
            f"\U0001f680 {owner}/{repo} - {tag_name}",
            f"\U0001f4dd {name}",
            f"\U0001f4c5 发布于: {published_at}",
            f"\U0001f4e6 下载: {zip_url}",
        ]
        return "\n".join(lines)

    async def _handle_latest_release(self, event: AstrMessageEvent, owner: str, repo: str):
        data = await self._fetch_api(f"/repos/{owner}/{repo}/releases/latest")
        if data is None:
            return
        if isinstance(data, dict) and data.get("error") == "rate_limited":
            yield event.plain_result("GitHub API 限流，请稍后再试")
            return
        yield event.plain_result(self._build_release_message(owner, repo, data))

    async def _handle_release_by_tag(self, event: AstrMessageEvent, owner: str, repo: str, tag: str):
        data = await self._fetch_api(f"/repos/{owner}/{repo}/releases/tags/{tag}")
        if data is None:
            return
        if isinstance(data, dict) and data.get("error") == "rate_limited":
            yield event.plain_result("GitHub API 限流，请稍后再试")
            return
        yield event.plain_result(self._build_release_message(owner, repo, data, tag))
