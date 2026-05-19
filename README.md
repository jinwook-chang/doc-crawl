# doc-crawl

Login-aware web crawler that renders pages with Crawl4AI, converts them to Markdown,
and downloads referenced images so the saved Markdown remains viewable offline.

## English

### What It Does

- Logs in to a website with Playwright through Crawl4AI hooks.
- Crawls the configured base URL and internal links up to a depth limit.
- Saves each crawled page as Markdown.
- Downloads images referenced in Markdown into a local `assets/` directory.
- Rewrites Markdown image links to local relative paths.
- Clears the output directory on each run so it always contains the latest crawl.

### Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Crawl4AI browser setup

### Setup

```bash
uv sync --dev
uv run crawl4ai-setup
```

Create a `.env` file:

```env
CRAWL_URL=https://a.com
LOGIN_URL=https://a.com/login
CRAWL_USERNAME=your-username
CRAWL_PASSWORD=your-password

USERNAME_SELECTOR=input[name="email"]
PASSWORD_SELECTOR=input[name="password"]
SUBMIT_SELECTOR=button[type="submit"]

CRAWL_MAX_DEPTH=0
OUTPUT_DIR=markdown
ASSETS_DIR=assets
HEADLESS=false
```

### Run

```bash
uv run crawl_to_markdown.py
```

### Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `CRAWL_URL` | Yes | - | Base URL to crawl after login. |
| `LOGIN_URL` | No | `CRAWL_URL` | Login page URL. |
| `CRAWL_USERNAME` | Yes | - | Username or email for login. |
| `CRAWL_PASSWORD` | Yes | - | Password for login. |
| `USERNAME_SELECTOR` | No | Common email/username selectors | Playwright selector for the username field. |
| `PASSWORD_SELECTOR` | No | Common password selectors | Playwright selector for the password field. |
| `SUBMIT_SELECTOR` | No | Common submit button selectors | Playwright selector for the login button. |
| `CRAWL_MAX_DEPTH` | No | `0` | Crawl depth. `0` saves only `CRAWL_URL`; `1` also saves links found on that page. |
| `OUTPUT_DIR` | No | `markdown` | Output directory. It is cleared at the start of each run. |
| `ASSETS_DIR` | No | `assets` | Image asset directory inside `OUTPUT_DIR`. |
| `HEADLESS` | No | `true` | Whether to run the browser headlessly. |
| `USER_DATA_DIR` | No | `.crawl4ai-profile` | Persistent browser profile directory. |
| `CRAWL_SESSION_ID` | No | `crawl4ai-login-session` | Crawl4AI session ID. |

### Lint

```bash
uv run ruff check .
```

### Notes

- The crawler follows same-domain links discovered by Crawl4AI.
- Login state is preserved in a persistent browser context.
- Images that fail to download are left as their original URLs in the Markdown.
- Be careful with authenticated crawls. Avoid crawling account settings, billing, logout,
  or destructive URLs.

## 한국어

### 기능

- Crawl4AI hook을 통해 Playwright로 로그인합니다.
- 로그인 후 설정한 base URL과 내부 링크를 지정한 depth까지 크롤링합니다.
- 각 페이지를 Markdown 파일로 저장합니다.
- Markdown에 포함된 이미지를 로컬 `assets/` 디렉터리에 다운로드합니다.
- Markdown 이미지 링크를 로컬 상대 경로로 바꿉니다.
- 실행할 때마다 출력 디렉터리를 비워 최신 결과만 남깁니다.

### 요구사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Crawl4AI 브라우저 설정

### 설치

```bash
uv sync --dev
uv run crawl4ai-setup
```

`.env` 파일을 만듭니다:

```env
CRAWL_URL=https://a.com
LOGIN_URL=https://a.com/login
CRAWL_USERNAME=your-username
CRAWL_PASSWORD=your-password

USERNAME_SELECTOR=input[name="email"]
PASSWORD_SELECTOR=input[name="password"]
SUBMIT_SELECTOR=button[type="submit"]

CRAWL_MAX_DEPTH=0
OUTPUT_DIR=markdown
ASSETS_DIR=assets
HEADLESS=false
```

### 실행

```bash
uv run crawl_to_markdown.py
```

### 설정

| 변수 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `CRAWL_URL` | 예 | - | 로그인 후 크롤링할 base URL입니다. |
| `LOGIN_URL` | 아니오 | `CRAWL_URL` | 로그인 페이지 URL입니다. |
| `CRAWL_USERNAME` | 예 | - | 로그인 아이디 또는 이메일입니다. |
| `CRAWL_PASSWORD` | 예 | - | 로그인 비밀번호입니다. |
| `USERNAME_SELECTOR` | 아니오 | 일반적인 아이디/이메일 selector | 아이디 입력칸의 Playwright selector입니다. |
| `PASSWORD_SELECTOR` | 아니오 | 일반적인 비밀번호 selector | 비밀번호 입력칸의 Playwright selector입니다. |
| `SUBMIT_SELECTOR` | 아니오 | 일반적인 submit 버튼 selector | 로그인 버튼의 Playwright selector입니다. |
| `CRAWL_MAX_DEPTH` | 아니오 | `0` | 크롤링 depth입니다. `0`은 `CRAWL_URL`만 저장하고, `1`은 해당 페이지에서 발견한 링크까지 저장합니다. |
| `OUTPUT_DIR` | 아니오 | `markdown` | 결과 저장 디렉터리입니다. 실행 시작 시 비워집니다. |
| `ASSETS_DIR` | 아니오 | `assets` | `OUTPUT_DIR` 안에 생성되는 이미지 저장 디렉터리입니다. |
| `HEADLESS` | 아니오 | `true` | 브라우저를 headless로 실행할지 여부입니다. |
| `USER_DATA_DIR` | 아니오 | `.crawl4ai-profile` | 영속 브라우저 프로필 디렉터리입니다. |
| `CRAWL_SESSION_ID` | 아니오 | `crawl4ai-login-session` | Crawl4AI session ID입니다. |

### 린트

```bash
uv run ruff check .
```

### 주의사항

- 크롤러는 Crawl4AI가 발견한 같은 도메인의 링크를 따라갑니다.
- 로그인 상태는 persistent browser context에 유지됩니다.
- 다운로드 실패한 이미지는 원본 URL 그대로 Markdown에 남습니다.
- 로그인된 상태로 크롤링하므로 계정 설정, 결제, 로그아웃, destructive URL을 밟지 않도록 주의하세요.
