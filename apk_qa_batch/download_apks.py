#!/usr/bin/env python3
"""Download APK files from provided URLs."""

import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

URLS = [
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e87d2aac-c2f5-4e0e-ba31-95638b619a22.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ae11d1d1-7f38-4e26-a33a-79f09da61f8c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/c9f4a477-8b69-4793-9a87-45f994732ec8.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/8751e382-d479-4851-bfe5-129fa51f75d6.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/73b3a9bd-64bc-40ed-9659-6780dbf40940.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2fb9a695-b338-4c7d-80ca-87edaa4c648a.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/fec72e4f-ecdb-44e3-87e3-00df90ffc8f4.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/40f32956-8e06-4ff1-a928-133e645f6ea8.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/8dd3daaf-d283-48ab-9822-cbb38029c63a.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/fbe95cd6-3640-4c1e-b619-fc63a1c38745.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/63aa3bb3-c9dd-47c0-8e63-61608c33e668.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2d31fe01-8032-4a05-80e3-b3b055d5acb9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/670f9323-9cd3-486e-a79c-19db11514999.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/d16f6846-8a1c-4d25-877d-79aad475501e.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/5b43043b-67b0-4b01-9ae8-4825e98ae597.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/aa4611c6-d5e8-4044-b958-ab5f70ffd02e.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/b4df0c0d-28b8-4191-a623-b8bcf321905c.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/d0ab38f1-e4d6-434a-ac39-ba3c3511a3fb.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/7bf58fd0-c814-4f3a-865c-0a89e88cff00.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/b8f5d6cd-c932-42fe-93dd-ede4f6d24c8f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/32f571ee-38bd-4478-ad40-493c83ae9159.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/88e65ab3-fcab-44f8-a226-0db16842cd5b.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/74007ba7-6139-4d78-9448-9d5125b563c5.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/da4fe19a-224a-44d6-bf98-3f1e3305605e.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/576e55ad-fc87-47eb-bff7-b525b425104b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/fce6e97f-f4e1-4be7-ae9e-3b6db25ca60f.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/7a54b72e-6fa5-4033-aa05-d974acd23fb9.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6a442a22-5e76-4e1a-a449-53dd8295bd76.apk",
]

def download_file(url, dest_dir):
    """Download a file from URL to destination directory."""
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(dest_dir, filename)
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filepath)
        print(f"[OK] {filename} ({file_size / 1024 / 1024:.1f} MB)")
        return {"url": url, "file": filepath, "size": file_size, "status": "success"}
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
        return {"url": url, "file": None, "error": str(e), "status": "error"}

def main():
    dest_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Downloading {len(URLS)} APK files to {dest_dir}...\n")
    
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(download_file, url, dest_dir): url for url in URLS}
        for future in as_completed(futures):
            results.append(future.result())
    
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    total_size = sum(r.get("size", 0) for r in results if r["status"] == "success")
    
    print(f"\n{'='*60}")
    print(f"Download Summary: {success}/{len(URLS)} successful, {failed} failed")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
