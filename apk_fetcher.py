"""
APK fetcher helper for Play Integrity Screener.
Pure-Python downloader — no external binaries required.

Download chain (tried in order):
  1. APKPure direct download endpoint
  2. APKCombo direct download endpoint
  3. APKPure scraping (search → app page → download link)

All methods share a requests.Session with a browser User-Agent.
"""

import os
import re
import tempfile
from urllib.parse import parse_qs, urljoin, urlparse

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================================
# Public API
# ============================================================================

def extract_package_name(input_str: str) -> str:
    """
    Accepts:
    - Full Play Store URL: https://play.google.com/store/apps/details?id=com.example.app
    - URL with extra params: ...?id=com.example.app&hl=en
    - Bare package name: com.example.app

    Returns the package name. Raises ValueError if unrecognized.
    """
    input_str = input_str.strip()

    if "play.google.com" in input_str:
        parsed = urlparse(input_str)
        params = parse_qs(parsed.query)
        if "id" in params:
            return params["id"][0]
        raise ValueError(f"No 'id' parameter found in Play Store URL: {input_str}")

    # Bare package name: contains dots, no spaces
    if "." in input_str and " " not in input_str:
        return input_str

    raise ValueError(
        f"Unrecognized input: {input_str!r}\n"
        "Expected a Google Play Store URL or a package name like com.example.app"
    )


def fetch_apk(package_name: str, output_dir: str) -> str:
    """
    Download an APK for *package_name* into *output_dir*.

    Tries three sources in order. Returns the local .apk path on success.
    Raises RuntimeError with a helpful message (including a manual download
    link) if all methods fail.
    """
    output_path = os.path.join(output_dir, f"{package_name}.apk")
    session = requests.Session()
    session.headers.update(_HEADERS)

    errors: list[str] = []

    # ── Method 1: APKPure direct endpoint ────────────────────────────────────
    try:
        url = f"https://d.apkpure.com/b/APK/{package_name}?version=latest"
        if _download_and_verify(session, url, output_path):
            return output_path
        errors.append("APKPure direct: response was not a valid APK")
    except Exception as exc:
        errors.append(f"APKPure direct: {exc}")

    # ── Method 2: APKCombo direct endpoint ───────────────────────────────────
    try:
        url = f"https://download.apkcombo.com/apk/{package_name}"
        if _download_and_verify(session, url, output_path):
            return output_path
        errors.append("APKCombo direct: response was not a valid APK")
    except Exception as exc:
        errors.append(f"APKCombo direct: {exc}")

    # ── Method 3: APKPure scraping ────────────────────────────────────────────
    try:
        dl_url = _scrape_apkpure(session, package_name)
        if dl_url and _download_and_verify(session, dl_url, output_path):
            return output_path
        errors.append("APKPure scrape: download link found but file was not a valid APK")
    except Exception as exc:
        errors.append(f"APKPure scrape: {exc}")

    # ── All methods failed ────────────────────────────────────────────────────
    error_detail = "\n".join(f"  • {e}" for e in errors)
    raise RuntimeError(
        f"Could not auto-download APK for '{package_name}'.\n\n"
        f"Attempted sources:\n{error_detail}\n\n"
        f"Download manually and use the 'Upload APK' option:\n"
        f"  https://apkpure.com/search?q={package_name}"
    )


# ============================================================================
# Internal helpers
# ============================================================================

def _download_and_verify(session: requests.Session, url: str, dest: str) -> bool:
    """
    Stream-download *url* to *dest*. Return True if the result is a valid APK
    (ZIP magic bytes PK). Delete *dest* and return False otherwise.
    """
    resp = session.get(url, allow_redirects=True, timeout=60, stream=True)
    if resp.status_code != 200:
        return False

    content_type = resp.headers.get("content-type", "")
    # Accept application/* or octet-stream; reject obvious HTML/JSON errors
    if "text/html" in content_type or "application/json" in content_type:
        return False

    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=65536):
            fh.write(chunk)

    # Verify ZIP magic bytes (APK = ZIP)
    with open(dest, "rb") as fh:
        magic = fh.read(2)

    if magic == b"PK":
        return True

    os.remove(dest)
    return False


def _scrape_apkpure(session: requests.Session, package_name: str) -> str | None:
    """
    Scrape APKPure to find a direct download URL for *package_name*.
    Returns the download URL string, or None if not found.
    """
    from bs4 import BeautifulSoup

    # Step 1: search
    search_url = f"https://apkpure.net/search?q={package_name}"
    resp = session.get(search_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find first result link whose href contains the package name
    app_path: str | None = None
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if package_name in href and "/download" not in href:
            # Normalise to absolute
            app_path = href if href.startswith("http") else urljoin("https://apkpure.net", href)
            break

    if not app_path:
        return None

    # Step 2: app download page
    dl_page_url = app_path.rstrip("/") + "/download"
    resp = session.get(dl_page_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Look for the primary download anchor
    for selector in [
        {"id": "download_link"},
        {"class": re.compile(r"download", re.I)},
        {"href": re.compile(r"\.apk", re.I)},
    ]:
        tag = soup.find("a", selector)
        if tag and tag.get("href"):
            href = tag["href"]
            return href if href.startswith("http") else urljoin(dl_page_url, href)

    return None
