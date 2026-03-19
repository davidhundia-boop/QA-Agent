"""
APK Fetcher — downloads APKs via multiple fallback strategies.

Install:  pip install apkpure requests beautifulsoup4 tqdm cloudscraper google-play-scraper

Strategies (in order):
  1. apkpure pip package — search by package name
  2. apkpure pip package — search by app title (via google-play-scraper)
  3. APKPure direct download URL (APK + XAPK)
  4. APKPure page scrape with cloudscraper (Cloudflare bypass)
  5. APKCombo page scrape
  6. apkeep binary (if installed)
"""

import os
import tempfile
import glob
import zipfile
from urllib.parse import urlparse, parse_qs


def extract_package_name(input_str: str) -> str:
    """
    Extract package name from a Play Store URL or bare package name.
    
    Accepts:
      - https://play.google.com/store/apps/details?id=com.example.app
      - https://play.google.com/store/apps/details?id=com.example.app&hl=en
      - play.google.com/store/apps/details?id=com.example.app
      - com.example.app
    """
    input_str = input_str.strip()
    
    # Handle URLs
    if 'play.google.com' in input_str:
        # Add scheme if missing
        if not input_str.startswith('http'):
            input_str = 'https://' + input_str
        parsed = urlparse(input_str)
        params = parse_qs(parsed.query)
        if 'id' in params:
            return params['id'][0]
        raise ValueError(f"No 'id' parameter found in URL: {input_str}")
    
    # Handle bare package name (contains dots, no spaces, no slashes)
    if '.' in input_str and ' ' not in input_str and '/' not in input_str:
        return input_str
    
    raise ValueError(
        f"Unrecognized input: '{input_str}'. "
        f"Paste a Google Play URL or a package name like 'com.example.app'"
    )


def fetch_apk(package_name: str, output_dir: str = None) -> str:
    """
    Download the latest APK for the given package name.
    Tries six strategies in order, falling back gracefully on each failure.

    Returns the path to a usable .apk file (XAPK bundles are unpacked automatically).
    Raises RuntimeError with a full error log if all strategies fail.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="apk_")
    os.makedirs(output_dir, exist_ok=True)

    errors = []

    # ── Strategy 1: apkpure pip package — search by package name ───────
    try:
        from apkpure.apkpure import ApkPure
        api = ApkPure()
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        try:
            path = api.download(package_name)
            if path and os.path.exists(path):
                return ensure_apk(os.path.abspath(path))
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        errors.append(f"apkpure (package name): {e}")

    # ── Strategy 2: apkpure pip package — search by app title ──────────
    try:
        from google_play_scraper import app as gplay_app
        info = gplay_app(package_name)
        app_title = info.get('title', '')
        if app_title:
            from apkpure.apkpure import ApkPure
            api = ApkPure()
            original_cwd = os.getcwd()
            os.chdir(output_dir)
            try:
                path = api.download(app_title)
                if path and os.path.exists(path):
                    return ensure_apk(os.path.abspath(path))
            finally:
                os.chdir(original_cwd)
    except Exception as e:
        errors.append(f"apkpure (app title): {e}")

    # ── Strategy 3: APKPure direct download URL (APK + XAPK) ───────────
    try:
        import requests
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            )
        }
        for fmt in ['APK', 'XAPK']:
            url = f"https://d.apkpure.com/b/{fmt}/{package_name}?version=latest"
            resp = requests.get(url, headers=headers, allow_redirects=True,
                                timeout=60, stream=True)
            content_type = resp.headers.get('content-type', '')
            if resp.status_code == 200 and (
                'octet-stream' in content_type or 'application' in content_type
            ):
                ext = '.xapk' if fmt == 'XAPK' else '.apk'
                output_path = os.path.join(output_dir, f"{package_name}{ext}")
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                if os.path.getsize(output_path) > 1000:
                    return ensure_apk(output_path)
                else:
                    os.remove(output_path)
    except Exception as e:
        errors.append(f"direct URL: {e}")

    # ── Strategy 4: APKPure page scrape (cloudscraper for Cloudflare) ──
    try:
        import cloudscraper
        from bs4 import BeautifulSoup

        scraper = cloudscraper.create_scraper()

        page_url = f"https://apkpure.com/search?q={package_name}"
        resp = scraper.get(page_url, timeout=30)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            app_link = soup.find("a", href=lambda h: h and package_name in h)
            if app_link:
                detail_url = app_link["href"]
                if not detail_url.startswith("http"):
                    detail_url = "https://apkpure.com" + detail_url

                for suffix in ["/download", "/downloading"]:
                    dl_page = scraper.get(detail_url + suffix, timeout=30)
                    if dl_page.status_code == 200:
                        dl_soup = BeautifulSoup(dl_page.text, "html.parser")
                        dl_link = dl_soup.find(
                            "a", href=lambda h: h and ("APK" in (h or "") or "download" in (h or "").lower()),
                            id=lambda i: i and "download" in (i or "").lower(),
                        )
                        if not dl_link:
                            dl_link = dl_soup.find("a", id="download_link")
                        if not dl_link:
                            dl_link = dl_soup.find(
                                "a", attrs={"data-dt-apkid": package_name}
                            )
                        if dl_link and dl_link.get("href"):
                            href = dl_link["href"]
                            if not href.startswith("http"):
                                href = "https://apkpure.com" + href
                            file_resp = scraper.get(href, timeout=120, stream=True)
                            ct = file_resp.headers.get("content-type", "")
                            if file_resp.status_code == 200 and (
                                "octet-stream" in ct or "application" in ct
                            ):
                                ext = ".xapk" if "xapk" in href.lower() else ".apk"
                                out = os.path.join(output_dir, f"{package_name}_scraped{ext}")
                                with open(out, "wb") as f:
                                    for chunk in file_resp.iter_content(8192):
                                        f.write(chunk)
                                if os.path.getsize(out) > 1000:
                                    return ensure_apk(out)
                                else:
                                    os.remove(out)
    except ImportError:
        errors.append("apkpure scrape: cloudscraper/bs4 not installed")
    except Exception as e:
        errors.append(f"apkpure scrape: {e}")

    # ── Strategy 5: APKCombo direct download ────────────────────────────
    try:
        import cloudscraper

        scraper = cloudscraper.create_scraper()
        combo_url = f"https://apkcombo.com/downloader/?package={package_name}"
        resp = scraper.get(combo_url, timeout=30)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            dl_links = soup.find_all("a", class_="variant")
            if not dl_links:
                dl_links = soup.find_all(
                    "a", href=lambda h: h and package_name in (h or "") and ".apk" in (h or "")
                )
            for link in dl_links:
                href = link.get("href", "")
                if not href:
                    continue
                if not href.startswith("http"):
                    href = "https://apkcombo.com" + href
                file_resp = scraper.get(href, timeout=120, stream=True)
                ct = file_resp.headers.get("content-type", "")
                if file_resp.status_code == 200 and (
                    "octet-stream" in ct or "application" in ct
                ):
                    ext = ".xapk" if "xapk" in href.lower() else ".apk"
                    out = os.path.join(output_dir, f"{package_name}_combo{ext}")
                    with open(out, "wb") as f:
                        for chunk in file_resp.iter_content(8192):
                            f.write(chunk)
                    if os.path.getsize(out) > 1000:
                        return ensure_apk(out)
                    else:
                        os.remove(out)
                        continue
    except ImportError:
        errors.append("apkcombo: cloudscraper/bs4 not installed")
    except Exception as e:
        errors.append(f"apkcombo: {e}")

    # ── Strategy 6: apkeep binary (if installed) ────────────────────────
    try:
        import subprocess
        result = subprocess.run(
            ['apkeep', '-a', package_name, output_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            apk_files = glob.glob(os.path.join(output_dir, '*.apk'))
            if apk_files:
                return ensure_apk(apk_files[0])
    except FileNotFoundError:
        pass
    except Exception as e:
        errors.append(f"apkeep: {e}")

    # ── All strategies failed ───────────────────────────────────────────
    error_log = "; ".join(errors) if errors else "no strategies returned a valid APK"
    raise RuntimeError(
        f"Could not download APK for '{package_name}'. "
        f"All download methods failed.\n"
        f"Debug: {error_log}\n\n"
        f"You can:\n"
        f"1. Download manually from https://apkpure.com/search?q={package_name}\n"
        f"2. Use the 'Upload APK' option below\n"
        f"3. Install extra fetchers: pip install apkpure cloudscraper beautifulsoup4"
    )


def fetch_apks_bulk(package_names: list, output_dir: str = None,
                     progress_callback=None) -> dict:
    """
    Download multiple APKs. Returns dict of results:
    {
        "com.example.app": {"status": "success", "path": "/tmp/.../app.apk"},
        "com.other.app": {"status": "failed", "error": "..."},
    }
    """
    import time
    
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="apk_bulk_")
    
    results = {}
    total = len(package_names)
    
    for i, pkg in enumerate(package_names):
        if progress_callback:
            progress_callback(i, total, pkg)
        
        try:
            apk_path = fetch_apk(pkg, output_dir)
            results[pkg] = {"status": "success", "path": apk_path}
        except Exception as e:
            results[pkg] = {"status": "failed", "error": str(e)}
        
        # Rate limit between downloads
        if i < total - 1:
            time.sleep(2)
    
    if progress_callback:
        progress_callback(total, total, "Done")
    
    return results


def ensure_apk(file_path: str) -> str:
    """
    If the file is a standard APK, return it as-is.
    If it's an XAPK (split APK bundle), extract the base APK and return that.

    Returns path to a usable .apk file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not zipfile.is_zipfile(file_path):
        raise RuntimeError(f"Not a valid APK or XAPK file: {file_path}")

    with zipfile.ZipFile(file_path, 'r') as zf:
        file_list = zf.namelist()

        # Regular APK — has DEX at the top level
        if 'classes.dex' in file_list:
            return file_path

        # XAPK — contains inner .apk files
        inner_apks = [f for f in file_list if f.endswith('.apk')]

        if not inner_apks:
            raise RuntimeError(
                f"File is a ZIP but contains no APKs or DEX files. "
                f"Contents: {file_list[:10]}"
            )

        # Strategy 1: base.apk (most common XAPK layout)
        base_apk = None
        if 'base.apk' in inner_apks:
            base_apk = 'base.apk'

        # Strategy 2: single non-config APK
        if not base_apk:
            non_config = [
                f for f in inner_apks
                if not f.startswith('config.') and not f.startswith('split_config.')
            ]
            if len(non_config) == 1:
                base_apk = non_config[0]

        # Strategy 3: find the APK that actually contains classes.dex
        # (handles Unity games where asset packs are larger than the base)
        if not base_apk:
            output_dir_tmp = os.path.dirname(file_path)
            for candidate in inner_apks:
                candidate_path = os.path.join(output_dir_tmp, f"_probe_{os.path.basename(candidate)}")
                try:
                    with zf.open(candidate) as src, open(candidate_path, 'wb') as dst:
                        dst.write(src.read())
                    if zipfile.is_zipfile(candidate_path):
                        with zipfile.ZipFile(candidate_path, 'r') as inner_zf:
                            if 'classes.dex' in inner_zf.namelist():
                                base_apk = candidate
                                os.remove(candidate_path)
                                break
                    os.remove(candidate_path)
                except Exception:
                    if os.path.exists(candidate_path):
                        os.remove(candidate_path)

        # Strategy 4: largest APK (last resort)
        if not base_apk:
            apk_sizes = [(name, zf.getinfo(name).file_size) for name in inner_apks]
            apk_sizes.sort(key=lambda x: x[1], reverse=True)
            base_apk = apk_sizes[0][0]

        # Extract the chosen APK
        output_dir = os.path.dirname(file_path)
        extracted_path = os.path.join(output_dir, f"base_{os.path.basename(base_apk)}")

        with zf.open(base_apk) as src, open(extracted_path, 'wb') as dst:
            dst.write(src.read())

        if zipfile.is_zipfile(extracted_path):
            with zipfile.ZipFile(extracted_path, 'r') as inner_zf:
                if 'classes.dex' in inner_zf.namelist():
                    return extracted_path

        raise RuntimeError(
            f"Extracted {base_apk} from XAPK but it doesn't contain classes.dex. "
            f"Inner APKs found: {inner_apks}. "
            f"The app may use an unusual packaging format."
        )
