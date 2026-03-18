"""
APK Fetcher — downloads APKs from APKPure using the 'apkpure' pip package.

Install:  pip install apkpure requests beautifulsoup4 tqdm cloudscraper

No external binaries needed (no apkeep, no cargo, no Rust).
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
    Download the latest APK for the given package name from APKPure.
    
    Returns the path to the downloaded APK file.
    Raises RuntimeError if download fails.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="apk_")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # ── Method 1: apkpure pip package ──────────────────────────────────
    try:
        from apkpure.apkpure import ApkPure
        
        api = ApkPure()
        
        # download() takes the package name or search term
        # It downloads to current working directory by default
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        try:
            download_path = api.download(package_name)
            if download_path and os.path.exists(download_path):
                # Verify it's a valid ZIP/APK
                with open(download_path, 'rb') as f:
                    magic = f.read(2)
                if magic == b'PK':
                    return ensure_apk(os.path.abspath(download_path))
                else:
                    os.remove(download_path)
                    raise RuntimeError("Downloaded file is not a valid APK")
        finally:
            os.chdir(original_cwd)
            
    except ImportError:
        pass  # apkpure not installed, try next method
    except Exception as e:
        # Log but don't fail — try fallback
        print(f"[apkpure package] Failed: {e}")
    
    # ── Method 2: apkeep binary (if available) ─────────────────────────
    try:
        import subprocess
        result = subprocess.run(
            ['apkeep', '-a', package_name, output_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            # apkeep may create files with various naming patterns
            apk_files = glob.glob(os.path.join(output_dir, '*.apk'))
            if apk_files:
                return ensure_apk(apk_files[0])
    except FileNotFoundError:
        pass  # apkeep not installed
    except Exception as e:
        print(f"[apkeep] Failed: {e}")
    
    # ── Method 3: Direct APKPure URL attempt ───────────────────────────
    try:
        import requests
        
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            )
        }
        
        # APKPure direct download endpoint
        url = f"https://d.apkpure.com/b/APK/{package_name}?version=latest"
        resp = requests.get(url, headers=headers, allow_redirects=True, 
                          timeout=60, stream=True)
        
        content_type = resp.headers.get('content-type', '')
        if resp.status_code == 200 and ('octet-stream' in content_type or 
                                         'apk' in content_type or
                                         'application' in content_type):
            output_path = os.path.join(output_dir, f"{package_name}.apk")
            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with open(output_path, 'rb') as f:
                magic = f.read(2)
            if magic == b'PK':
                return ensure_apk(output_path)
            else:
                os.remove(output_path)
    except Exception as e:
        print(f"[direct download] Failed: {e}")
    
    # ── All methods failed ─────────────────────────────────────────────
    raise RuntimeError(
        f"Could not download APK for '{package_name}'.\n\n"
        f"All download methods failed. You can:\n"
        f"1. Download manually from https://apkpure.com/search?q={package_name}\n"
        f"2. Use the 'Upload APK' option below\n"
        f"3. Install the apkpure package: pip install apkpure"
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

        # Strategy 3: largest APK
        if not base_apk:
            apk_sizes = [(name, zf.getinfo(name).file_size) for name in inner_apks]
            apk_sizes.sort(key=lambda x: x[1], reverse=True)
            base_apk = apk_sizes[0][0]

        # Extract
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
            f"The app may use an unusual packaging format."
        )
