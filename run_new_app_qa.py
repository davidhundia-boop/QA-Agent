#!/usr/bin/env python3
"""
New App QA Script - Downloads and analyzes APKs from URLs for Play Integrity issues.
"""

import os
import sys
import json
import zipfile
import csv
from datetime import datetime

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from play_integrity_analyzer import PlayIntegrityAnalyzer

APK_URLS = [
    "https://whitelabel-cdn-prod.digitalturbine.com/files/eeb930c0-6f00-4c40-a939-e3bc7b0f5633.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/96c1ca41-464d-4663-9718-fd8fff67e87b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ae11d1d1-7f38-4e26-a33a-79f09da61f8c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/4719285a-3148-41bc-857c-5e95c5607a4a.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/fc2d326e-08e6-4dde-99c7-e12244d7c541.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/197e50b2-1e91-4206-b8e7-9e2ec217c962.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/80350746-05e6-48a0-9038-cf6f21c0f03d.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/97448af4-cdfc-40f9-8f51-268507b83c56.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/b002443c-6179-4a50-b7a9-ab37b1d4e2ed.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2ff097e4-09bd-4e64-a924-64d635163b2e.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/fa8416f9-814e-4992-bf89-f043707af45e.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/afe0900e-42af-49dc-acaf-d29c916f8f87.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/0d92ee82-e7dc-4f71-865c-e11bbaa6a56f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/43b692f7-ee89-44f1-b35b-914542306871.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/a5af2978-c347-4728-aaee-0fbac262a849.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/8b1b42c7-5e9d-42d0-8a82-eab0b0a1f8ca.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/aeefdba6-6976-48dc-a9de-f7d18d93073e.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/39f85c2d-3626-47bb-967a-44945909abbe.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/60b77d0f-3964-423c-963c-fb2fdcb3453e.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/f7941492-0f9a-4864-8c80-24d5345d53d7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/78ef2a9b-2050-4a6e-99e7-cc516b056fca.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/7bab6bba-1f42-4bc9-991c-b97a28da357f.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/018300fc-723b-4b0a-9bba-ef63b2087650.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/19db8b7d-13b1-41ce-810e-a571e6c6b156.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/5b4f3d01-81a3-4236-b0d1-1621fa903546.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/3fa5ea41-d517-4396-bc73-729712b7d7fd.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/faf3b50f-3661-4b3b-8d53-3b676dfc6cec.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/f50a398d-c336-4a65-a5fd-0093c96df8b7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/a49dff16-a984-4d8d-b177-ec4eb26c470a.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/c97b2daa-508a-4f60-baa6-4f33e4e700ef.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/97a321a8-668c-461b-9f2c-159564a5e9b7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/052188bc-4dbb-4236-8a85-3880007488e7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/672eb6b4-212c-41d2-9d05-12fb3e962940.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/bd1513aa-02e5-453d-902c-0aa6acf90196.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/43741570-1c57-4f95-b3dc-41ad614cc207.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6937eae8-3a9e-4e8a-a3c8-833084bf08bf.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/160a805e-2fdd-4751-b1a4-b140cb51fcc2.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/91141955-a716-49b0-940c-de88bb11e660.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/07f802dd-62c0-4fe4-a8cf-1cfdfd8761a3.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/deefd7ef-3695-427b-9f75-c3261c24338e.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/4893a56c-eac7-4bed-ab03-d61e144073ce.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/679c5073-3112-4cc0-a36f-d40029bc0ee7.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/8537dab5-b37e-44ee-8493-61433f72ce97.apk",
]


def download_file(url: str, dest_path: str, timeout: int = 120) -> bool:
    """Download a file from URL to destination path."""
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  [!] Download failed: {e}")
        return False


def extract_base_apk_from_apks(apks_path: str, output_dir: str) -> str:
    """Extract base APK from an .apks bundle (zip format)."""
    try:
        with zipfile.ZipFile(apks_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.apk') and 'base' in name.lower():
                    extracted_path = os.path.join(output_dir, os.path.basename(name))
                    with zf.open(name) as src, open(extracted_path, 'wb') as dst:
                        dst.write(src.read())
                    return extracted_path
            for name in zf.namelist():
                if name.lower().endswith('.apk'):
                    extracted_path = os.path.join(output_dir, os.path.basename(name))
                    with zf.open(name) as src, open(extracted_path, 'wb') as dst:
                        dst.write(src.read())
                    return extracted_path
    except Exception as e:
        print(f"  [!] APKS extraction failed: {e}")
    return apks_path


def analyze_single_apk(url: str, index: int, total: int, output_dir: str) -> dict:
    """Download and analyze a single APK/APKS file."""
    file_id = url.split('/')[-1]
    is_apks = url.endswith('.apks')
    local_path = os.path.join(output_dir, file_id)
    
    print(f"\n[{index}/{total}] Processing {file_id}...")
    
    result = {
        "url": url,
        "file_id": file_id,
        "is_apks": is_apks,
        "download_success": False,
        "analysis_success": False,
        "verdict": "ERROR",
        "package": "unknown",
        "app_name": "unknown",
        "fail_reasons": [],
        "warning_reasons": [],
        "error": None,
        "dex_string_count": 0,
        "play_integrity_detected": False,
    }
    
    print(f"  Downloading...")
    if not download_file(url, local_path):
        result["error"] = "Download failed"
        return result
    result["download_success"] = True
    
    apk_to_analyze = local_path
    if is_apks:
        print(f"  Extracting base APK from APKS bundle...")
        apk_to_analyze = extract_base_apk_from_apks(local_path, output_dir)
    
    print(f"  Analyzing...")
    try:
        analyzer = PlayIntegrityAnalyzer(apk_to_analyze)
        analyzer.analyze()
        json_result = analyzer.to_json()
        
        result["analysis_success"] = True
        result["verdict"] = json_result.get("verdict", "ERROR")
        result["package"] = json_result.get("package", "unknown")
        result["app_name"] = json_result.get("app_name", "unknown")
        result["dex_string_count"] = json_result.get("dex_string_count", 0)
        result["play_integrity_detected"] = json_result.get("play_integrity_detected", False)
        
        details = json_result.get("details", {})
        for fail_item in details.get("fail", []):
            result["fail_reasons"].append(fail_item.get("name", "Unknown"))
        for warn_item in details.get("warning", []):
            result["warning_reasons"].append(warn_item.get("name", "Unknown"))
            
    except Exception as e:
        result["error"] = str(e)
        print(f"  [!] Analysis failed: {e}")
    
    return result


def generate_report(results: list, output_path: str):
    """Generate a CSV report of all results."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "File ID", "Package Name", "App Name", "Verdict", 
            "Fail Reasons", "Warning Reasons", "Is APKS", 
            "Download Success", "Analysis Success", "Error", "URL"
        ])
        for r in results:
            writer.writerow([
                r["file_id"],
                r["package"],
                r["app_name"],
                r["verdict"],
                "; ".join(r["fail_reasons"]) if r["fail_reasons"] else "",
                "; ".join(r["warning_reasons"]) if r["warning_reasons"] else "",
                "Yes" if r["is_apks"] else "No",
                "Yes" if r["download_success"] else "No",
                "Yes" if r["analysis_success"] else "No",
                r["error"] or "",
                r["url"],
            ])


def print_summary(results: list):
    """Print a summary of the analysis results."""
    total = len(results)
    verdicts = {"PASS": 0, "WARNING": 0, "FAIL": 0, "INCONCLUSIVE": 0, "ERROR": 0}
    
    for r in results:
        verdict = r["verdict"]
        if verdict in verdicts:
            verdicts[verdict] += 1
        else:
            verdicts["ERROR"] += 1
    
    print("\n" + "=" * 70)
    print("  NEW APP QA SUMMARY")
    print("=" * 70)
    print(f"  Total APKs analyzed: {total}")
    print(f"  PASS:         {verdicts['PASS']}")
    print(f"  WARNING:      {verdicts['WARNING']}")
    print(f"  FAIL:         {verdicts['FAIL']}")
    print(f"  INCONCLUSIVE: {verdicts['INCONCLUSIVE']}")
    print(f"  ERROR:        {verdicts['ERROR']}")
    print("=" * 70)
    
    if verdicts['FAIL'] > 0:
        print("\n  FAILED APKs (will block DT preloads):")
        print("-" * 70)
        for r in results:
            if r["verdict"] == "FAIL":
                reasons = ", ".join(r["fail_reasons"]) if r["fail_reasons"] else "See report"
                print(f"    - {r['package']} ({r['app_name']})")
                print(f"      Reason: {reasons}")
    
    if verdicts['WARNING'] > 0:
        print("\n  WARNING APKs (needs manual verification):")
        print("-" * 70)
        for r in results:
            if r["verdict"] == "WARNING":
                reasons = ", ".join(r["warning_reasons"]) if r["warning_reasons"] else "See report"
                print(f"    - {r['package']} ({r['app_name']})")
                print(f"      Reason: {reasons}")
    
    if verdicts['ERROR'] > 0 or verdicts['INCONCLUSIVE'] > 0:
        print("\n  ERROR/INCONCLUSIVE APKs (could not fully analyze):")
        print("-" * 70)
        for r in results:
            if r["verdict"] in ("ERROR", "INCONCLUSIVE"):
                error_msg = r.get("error", "Unknown error")
                print(f"    - {r['file_id']}: {error_msg}")
    
    print()


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"/workspace/qa_apks/run_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("  New App QA - Play Integrity Analysis")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total APKs to analyze: {len(APK_URLS)}")
    print(f"  Output directory: {output_dir}")
    print("=" * 70)
    
    results = []
    total = len(APK_URLS)
    
    for idx, url in enumerate(APK_URLS, 1):
        result = analyze_single_apk(url, idx, total, output_dir)
        results.append(result)
    
    report_path = os.path.join(output_dir, "qa_report.csv")
    generate_report(results, report_path)
    print(f"\n  CSV report saved to: {report_path}")
    
    json_path = os.path.join(output_dir, "qa_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  JSON results saved to: {json_path}")
    
    print_summary(results)
    
    return results


if __name__ == "__main__":
    results = main()
