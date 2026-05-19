# doc-crawl

Login-aware web crawler that uses Playwright for browser automation and Docling for
rendered HTML to Markdown conversion. Images referenced by the rendered page are
downloaded locally and wired back into the saved Markdown.

## English

### What It Does

- Logs in to a website with Playwright.
- Crawls the configured base URL and same-domain internal links up to a depth limit.
- Converts rendered HTML to Markdown with Docling.
- Downloads page images into a local `assets/` directory.
- Replaces Docling image placeholders with local Markdown image links.
- Clears the output directory on each run so it always contains the latest crawl.

### Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Playwright Chromium

### Setup

```bash
uv sync --dev
uv run playwright install chromium
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

CRAWL_MAX_DEPTH=3
OUTPUT_DIR=markdown
ASSETS_DIR=assets
HEADLESS=false
USER_DATA_DIR=.playwright-profile
```

The script loads `.env` into `os.environ`. If any required value is missing or empty,
the script exits with an error.

### Run

```bash
uv run crawl_to_markdown.py
```

### Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `CRAWL_URL` | Yes | Base URL to crawl after login. |
| `LOGIN_URL` | Yes | Login page URL. |
| `CRAWL_USERNAME` | Yes | Username or email for login. |
| `CRAWL_PASSWORD` | Yes | Password for login. |
| `USERNAME_SELECTOR` | Yes | Playwright selector for the username field. |
| `PASSWORD_SELECTOR` | Yes | Playwright selector for the password field. |
| `SUBMIT_SELECTOR` | Yes | Playwright selector for the login button. |
| `CRAWL_MAX_DEPTH` | Yes | Crawl depth. `0` saves only `CRAWL_URL`; `1` also saves links found on that page. |
| `OUTPUT_DIR` | Yes | Output directory. It is cleared at the start of each run. |
| `ASSETS_DIR` | Yes | Image asset directory inside `OUTPUT_DIR`. |
| `HEADLESS` | Yes | Whether to run Chromium headlessly. |
| `USER_DATA_DIR` | Yes | Persistent Playwright browser profile directory. |

### How Conversion Works

The script uses Playwright to load the authenticated, JavaScript-rendered page and
passes the resulting HTML to Docling. Docling converts that HTML into Markdown. Since
Docling's HTML export can emit image placeholders instead of preserving image URLs,
the script separately collects rendered `<img>` elements, downloads them with the
authenticated browser cookies, and replaces image placeholders with local Markdown
image links.

### Lint

```bash
uv run ruff check .
```

### Notes

- The crawler follows same-domain links discovered from the rendered page.
- Login state is preserved in a persistent Playwright context.
- Images that fail to download are skipped, leaving Docling's image placeholder in place.
- Be careful with authenticated crawls. Avoid crawling account settings, billing, logout,
  or destructive URLs.

## 한국어

### 기능

- Playwright로 로그인합니다.
- 로그인 후 설정한 base URL과 같은 도메인의 내부 링크를 지정한 depth까지 크롤링합니다.
- 렌더링된 HTML을 Docling으로 Markdown 변환합니다.
- 페이지 이미지를 로컬 `assets/` 디렉터리에 다운로드합니다.
- Docling 이미지 placeholder를 로컬 Markdown 이미지 링크로 바꿉니다.
- 실행할 때마다 출력 디렉터리를 비워 최신 결과만 남깁니다.

### 요구사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Playwright Chromium

### 설치

```bash
uv sync --dev
uv run playwright install chromium
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

CRAWL_MAX_DEPTH=3
OUTPUT_DIR=markdown
ASSETS_DIR=assets
HEADLESS=false
USER_DATA_DIR=.playwright-profile
```

스크립트는 `.env` 값을 `os.environ`에 로드합니다. 필수 값이 없거나 비어 있으면 오류를 내고 종료합니다.

### 실행

```bash
uv run crawl_to_markdown.py
```

### 설정

| 변수 | 필수 | 설명 |
| --- | --- | --- |
| `CRAWL_URL` | 예 | 로그인 후 크롤링할 base URL입니다. |
| `LOGIN_URL` | 예 | 로그인 페이지 URL입니다. |
| `CRAWL_USERNAME` | 예 | 로그인 아이디 또는 이메일입니다. |
| `CRAWL_PASSWORD` | 예 | 로그인 비밀번호입니다. |
| `USERNAME_SELECTOR` | 예 | 아이디 입력칸의 Playwright selector입니다. |
| `PASSWORD_SELECTOR` | 예 | 비밀번호 입력칸의 Playwright selector입니다. |
| `SUBMIT_SELECTOR` | 예 | 로그인 버튼의 Playwright selector입니다. |
| `CRAWL_MAX_DEPTH` | 예 | 크롤링 depth입니다. `0`은 `CRAWL_URL`만 저장하고, `1`은 해당 페이지에서 발견한 링크까지 저장합니다. |
| `OUTPUT_DIR` | 예 | 결과 저장 디렉터리입니다. 실행 시작 시 비워집니다. |
| `ASSETS_DIR` | 예 | `OUTPUT_DIR` 안에 생성되는 이미지 저장 디렉터리입니다. |
| `HEADLESS` | 예 | Chromium을 headless로 실행할지 여부입니다. |
| `USER_DATA_DIR` | 예 | 영속 Playwright 브라우저 프로필 디렉터리입니다. |

### 변환 방식

스크립트는 Playwright로 로그인된 JavaScript 렌더링 페이지를 열고, 그 결과 HTML을
Docling에 넘겨 Markdown으로 변환합니다. Docling의 HTML 변환은 이미지 URL을 그대로
Markdown 이미지로 보존하지 않고 placeholder를 낼 수 있기 때문에, 스크립트가 별도로
렌더링된 `<img>` 요소를 수집하고 로그인 쿠키로 이미지를 다운로드한 뒤 placeholder를
로컬 Markdown 이미지 링크로 바꿉니다.

### 린트

```bash
uv run ruff check .
```

### 주의사항

- 크롤러는 렌더링된 페이지에서 발견한 같은 도메인의 링크를 따라갑니다.
- 로그인 상태는 persistent Playwright context에 유지됩니다.
- 다운로드 실패한 이미지는 건너뛰며, 해당 위치에는 Docling placeholder가 남을 수 있습니다.
- 로그인된 상태로 크롤링하므로 계정 설정, 결제, 로그아웃, destructive URL을 밟지 않도록 주의하세요.
