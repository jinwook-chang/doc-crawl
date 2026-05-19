#!/usr/bin/env python3
"""
Crawl a login-protected site with Playwright and convert rendered HTML to Markdown with Docling.

Install:
  uv sync --dev
  uv run playwright install chromium

.env example:
  CRAWL_URL=https://a.com
  CRAWL_USERNAME=you@example.com
  CRAWL_PASSWORD=secret

Optional:
  LOGIN_URL=https://a.com/login
  USERNAME_SELECTOR=input[name="email"]
  PASSWORD_SELECTOR=input[name="password"]
  SUBMIT_SELECTOR=button[type="submit"]
  CONTENT_SELECTOR=main
  CRAWL_MAX_DEPTH=0
  OUTPUT_DIR=markdown
  ASSETS_DIR=assets
  HEADLESS=false

Run:
  uv run crawl_to_markdown.py

Lint:
  uv run ruff check .
"""

from __future__ import annotations

import asyncio
import hashlib
import mimetypes
import os
import re
import shutil
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from docling.document_converter import DocumentConverter
from docling_core.types.io import DocumentStream
from playwright.async_api import Page, async_playwright

DEFAULT_USERNAME_SELECTORS = [
    'input[name="email"]',
    'input[type="email"]',
    'input[name="username"]',
    'input[name="userId"]',
    'input[id*="email" i]',
    'input[id*="user" i]',
]

DEFAULT_PASSWORD_SELECTORS = [
    'input[name="password"]',
    'input[type="password"]',
    'input[id*="password" i]',
    'input[id*="pass" i]',
]

DEFAULT_SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("로그인")',
    'button:has-text("Sign in")',
    'button:has-text("Login")',
]

IMAGE_PLACEHOLDER = "<!-- image -->"


def load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required env value: {name}")
    return value


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer, got: {value}") from exc


def selectors(env_name: str, defaults: Iterable[str]) -> list[str]:
    value = os.getenv(env_name)
    if not value:
        return list(defaults)
    return [item.strip() for item in value.split(",") if item.strip()]


def reset_output_dir(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    cwd = Path.cwd().resolve()
    dangerous_paths = {Path("/").resolve(), cwd, Path.home().resolve()}

    if resolved in dangerous_paths:
        raise SystemExit(f"Refusing to clear unsafe OUTPUT_DIR: {resolved}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


async def fill_first(page: Page, selector_list: Iterable[str], value: str, label: str) -> None:
    for selector in selector_list:
        locator = page.locator(selector).first
        try:
            if await locator.count() > 0 and await locator.is_visible(timeout=1500):
                await locator.fill(value)
                return
        except Exception:
            continue

    raise RuntimeError(
        f"Could not find a visible {label} input. Set {label.upper()}_SELECTOR in .env."
    )


async def click_first(page: Page, selector_list: Iterable[str]) -> None:
    for selector in selector_list:
        locator = page.locator(selector).first
        try:
            if await locator.count() > 0 and await locator.is_visible(timeout=1500):
                await locator.click()
                return
        except Exception:
            continue

    await page.keyboard.press("Enter")


def safe_filename(url: str, index: int) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "index"
    name = f"{parsed.netloc}-{path}"
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return f"{index:04d}-{name[:160]}.md"


def safe_stem(url: str, index: int) -> str:
    return Path(safe_filename(url, index)).stem


def normalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None
    url = urldefrag(urljoin(base_url, href))[0]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    return url


def same_site(seed_url: str, candidate_url: str) -> bool:
    seed = urlparse(seed_url)
    candidate = urlparse(candidate_url)
    return seed.netloc == candidate.netloc


def image_extension(url: str, content_type: str | None) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif"}:
        return suffix

    if content_type:
        media_type = content_type.split(";", 1)[0].strip().lower()
        guessed = mimetypes.guess_extension(media_type)
        if guessed:
            return ".jpg" if guessed == ".jpe" else guessed

    return ".img"


def apply_cookie_state(client: httpx.AsyncClient, cookies: list[dict]) -> None:
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        domain = cookie.get("domain")
        path = cookie.get("path", "/")
        if name and value is not None and domain:
            client.cookies.set(name, value, domain=domain, path=path)


def html_to_markdown(converter: DocumentConverter, html: str, source_name: str) -> str:
    stream = DocumentStream(name=source_name, stream=BytesIO(html.encode("utf-8")))
    result = converter.convert(stream)
    return result.document.export_to_markdown(image_placeholder=IMAGE_PLACEHOLDER)


async def extract_rendered_content(page: Page, content_selector: str | None) -> dict:
    if content_selector:
        locator = page.locator(content_selector).first
        if await locator.count() == 0:
            raise RuntimeError(f"CONTENT_SELECTOR did not match anything: {content_selector}")
        return await locator.evaluate(
            """element => ({
                html: element.outerHTML,
                links: Array.from(element.querySelectorAll('a[href]')).map(a => a.href),
                images: Array.from(element.querySelectorAll('img[src]')).map(img => ({
                    src: img.currentSrc || img.src,
                    alt: img.alt || ''
                }))
            })"""
        )

    html = await page.content()
    links = await page.eval_on_selector_all("a[href]", "links => links.map(a => a.href)")
    images = await page.eval_on_selector_all(
        "img[src]",
        """images => images.map(img => ({
            src: img.currentSrc || img.src,
            alt: img.alt || ''
        }))""",
    )
    return {"html": html, "links": links, "images": images}


def extract_internal_links(seed_url: str, page_url: str, links: Iterable[str]) -> list[str]:
    urls: list[str] = []
    for href in links:
        url = normalize_url(page_url, href)
        if url and same_site(seed_url, url):
            urls.append(url)
    return urls


async def download_images(
    images: list[dict],
    page_url: str,
    output_dir: Path,
    assets_dir_name: str,
    page_stem: str,
    cookies: list[dict],
) -> list[str]:
    if not images:
        return []

    page_assets_dir = output_dir / assets_dir_name / page_stem
    page_assets_dir.mkdir(parents=True, exist_ok=True)
    markdown_images: list[str] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        apply_cookie_state(client, cookies)

        for image in images:
            raw_url = str(image.get("src") or "")
            absolute_url = normalize_url(page_url, raw_url)
            if not absolute_url or absolute_url in seen:
                continue
            seen.add(absolute_url)

            try:
                response = await client.get(absolute_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"[image-skip] {absolute_url}: {exc}")
                continue

            digest = hashlib.sha1(absolute_url.encode("utf-8")).hexdigest()[:12]
            extension = image_extension(absolute_url, response.headers.get("content-type"))
            image_path = page_assets_dir / f"{digest}{extension}"
            image_path.write_bytes(response.content)

            relative_path = image_path.relative_to(output_dir).as_posix()
            alt_text = str(image.get("alt") or image_path.stem).replace("\n", " ").strip()
            markdown_images.append(f"![{alt_text}]({relative_path})")
            print(f"[image] {absolute_url} -> {relative_path}")

    return markdown_images


def replace_image_placeholders(markdown: str, markdown_images: list[str]) -> str:
    if not markdown_images:
        return markdown

    remaining = iter(markdown_images)

    def replace_once(match: re.Match[str]) -> str:
        return next(remaining, match.group(0))

    return re.sub(re.escape(IMAGE_PLACEHOLDER), replace_once, markdown)


async def login(page: Page, login_url: str, username: str, password: str) -> None:
    print(f"[login] opening {login_url}")
    await page.goto(login_url, wait_until="domcontentloaded")
    await fill_first(
        page,
        selectors("USERNAME_SELECTOR", DEFAULT_USERNAME_SELECTORS),
        username,
        "username",
    )
    await fill_first(
        page,
        selectors("PASSWORD_SELECTOR", DEFAULT_PASSWORD_SELECTORS),
        password,
        "password",
    )
    await click_first(page, selectors("SUBMIT_SELECTOR", DEFAULT_SUBMIT_SELECTORS))
    await page.wait_for_load_state("networkidle", timeout=30000)
    print("[login] complete")


async def main() -> None:
    load_env()

    crawl_url = required_env("CRAWL_URL")
    username = required_env("CRAWL_USERNAME")
    password = required_env("CRAWL_PASSWORD")

    login_url = os.getenv("LOGIN_URL", crawl_url)
    output_dir = Path(os.getenv("OUTPUT_DIR", "markdown"))
    reset_output_dir(output_dir)

    assets_dir_name = os.getenv("ASSETS_DIR", "assets")
    content_selector = os.getenv("CONTENT_SELECTOR") or None
    max_depth = max(0, env_int("CRAWL_MAX_DEPTH", 0))
    profile_dir = os.getenv("USER_DATA_DIR", str(Path(".playwright-profile").resolve()))
    headless = env_bool("HEADLESS", True)

    converter = DocumentConverter()
    queue = [(crawl_url, 0)]
    queued = {crawl_url}
    seen: set[str] = set()
    saved = 0

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
        )
        page = await context.new_page()

        try:
            await login(page, login_url, username, password)
            auth_cookies = await context.cookies()

            while queue:
                url, depth = queue.pop(0)
                queued.discard(url)
                if url in seen:
                    continue
                seen.add(url)

                print(f"[crawl] depth={depth} {url}")
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=30000)

                content = await extract_rendered_content(page, content_selector)
                page_index = saved + 1
                page_stem = safe_stem(url, page_index)
                markdown = html_to_markdown(converter, content["html"], f"{page_stem}.html")
                markdown_images = await download_images(
                    images=content["images"],
                    page_url=url,
                    output_dir=output_dir,
                    assets_dir_name=assets_dir_name,
                    page_stem=page_stem,
                    cookies=auth_cookies,
                )
                markdown = replace_image_placeholders(markdown, markdown_images)

                output_path = output_dir / safe_filename(url, page_index)
                output_path.write_text(markdown, encoding="utf-8")
                saved += 1
                print(f"[save] {output_path}")

                if depth < max_depth:
                    for next_url in extract_internal_links(crawl_url, url, content["links"]):
                        if next_url not in seen and next_url not in queued:
                            queue.append((next_url, depth + 1))
                            queued.add(next_url)
        finally:
            await context.close()

    print(f"[done] saved {saved} markdown file(s) to {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
