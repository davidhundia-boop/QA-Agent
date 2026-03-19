#!/usr/bin/env python3
"""
Batch App QA Script

Downloads APK/APKS files from direct URLs and runs comprehensive QA analysis:
- Play Integrity analysis (detects blocking protections)
- Wake Lock analysis (detects screen-wake patterns)

Supports both .apk and .apks (split APK bundle) formats.
"""

import csv
import json
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import unquote, urlparse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from play_integrity_analyzer import PlayIntegrityAnalyzer
from wake_lock_analyzer import analyze_apk as analyze_wake_lock


@dataclass
class AppQAResult:
    url: str
    filename: str
    file_type: str  # "apk" or "apks"
    package_name: Optional[str] = None
    app_name: Optional[str] = None
    
    # Download status
    download_success: bool = False
    download_error: Optional[str] = None
    file_size_mb: Optional[float] = None
    
    # Play Integrity results
    pi_verdict: str = "ERROR"
    pi_fail_reasons: list = field(default_factory=list)
    pi_warning_reasons: list = field(default_factory=list)
    pi_error: Optional[str] = None
    
    # Wake Lock results
    wl_detected: bool = False
    wl_confidence: str = "N/A"
    wl_needs_review: str = "No"
    wl_reasons: list = field(default_factory=list)
    wl_comment: Optional[str] = None
    wl_error: Optional[str] = None
    
    # Overall QA verdict
    qa_verdict: str = "ERROR"
    qa_notes: list = field(default_factory=list)


def download_file(url: str, dest_path: str, timeout: int = 120) -> tuple[bool, str]:
    """Download a file from URL to destination path."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, ""
    except requests.exceptions.RequestException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def extract_apks_bundle(apks_path: str, output_dir: str) -> list[str]:
    """Extract APK files from an APKS bundle (ZIP format)."""
    apk_files = []
    try:
        with zipfile.ZipFile(apks_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.apk'):
                    extracted_path = os.path.join(output_dir, os.path.basename(name))
                    with zf.open(name) as src, open(extracted_path, 'wb') as dst:
                        dst.write(src.read())
                    apk_files.append(extracted_path)
    except Exception as e:
        print(f"Error extracting APKS bundle: {e}")
    return apk_files


def get_filename_from_url(url: str) -> str:
    """Extract filename from URL."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    if not filename:
        filename = parsed.path.split('/')[-1] or "unknown"
    return filename


def run_play_integrity_analysis(apk_path: str) -> dict:
    """Run Play Integrity analysis on an APK."""
    try:
        analyzer = PlayIntegrityAnalyzer(apk_path)
        analyzer.analyze()
        return analyzer.to_json()
    except Exception as e:
        return {"verdict": "ERROR", "error": str(e), "details": {"fail": [], "warning": []}}


def run_wake_lock_analysis(apk_path: str) -> dict:
    """Run Wake Lock analysis on an APK."""
    try:
        return analyze_wake_lock(apk_path)
    except Exception as e:
        return {"error": str(e), "wake_lock_detected": False, "confidence": "N/A"}


def analyze_app(url: str, work_dir: str) -> AppQAResult:
    """Download and analyze a single app."""
    filename = get_filename_from_url(url)
    file_type = "apks" if filename.lower().endswith('.apks') else "apk"
    
    result = AppQAResult(
        url=url,
        filename=filename,
        file_type=file_type,
    )
    
    # Download the file
    download_path = os.path.join(work_dir, filename)
    success, error = download_file(url, download_path)
    
    if not success:
        result.download_success = False
        result.download_error = error
        result.qa_verdict = "DOWNLOAD_ERROR"
        result.qa_notes.append(f"Download failed: {error}")
        return result
    
    result.download_success = True
    result.file_size_mb = round(os.path.getsize(download_path) / (1024 * 1024), 2)
    
    # Get APK path(s) for analysis
    apk_paths = []
    if file_type == "apks":
        extract_dir = os.path.join(work_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        apk_paths = extract_apks_bundle(download_path, extract_dir)
        if not apk_paths:
            result.qa_verdict = "EXTRACTION_ERROR"
            result.qa_notes.append("Failed to extract APKs from bundle")
            return result
        # Find base APK (usually the largest or named "base")
        base_apk = None
        for p in apk_paths:
            if "base" in os.path.basename(p).lower():
                base_apk = p
                break
        if not base_apk:
            base_apk = max(apk_paths, key=os.path.getsize)
        apk_for_analysis = base_apk
    else:
        apk_for_analysis = download_path
        apk_paths = [download_path]
    
    # Run Play Integrity analysis
    try:
        pi_result = run_play_integrity_analysis(apk_for_analysis)
        result.pi_verdict = pi_result.get("verdict", "ERROR")
        result.package_name = pi_result.get("package", "unknown")
        result.app_name = pi_result.get("app_name", "unknown")
        
        details = pi_result.get("details", {})
        result.pi_fail_reasons = [r.get("name", "") for r in details.get("fail", [])]
        result.pi_warning_reasons = [r.get("name", "") for r in details.get("warning", [])]
        
        if pi_result.get("error"):
            result.pi_error = pi_result["error"]
    except Exception as e:
        result.pi_verdict = "ERROR"
        result.pi_error = str(e)
    
    # Run Wake Lock analysis
    try:
        wl_result = run_wake_lock_analysis(apk_for_analysis)
        result.wl_detected = wl_result.get("wake_lock_detected", False)
        result.wl_confidence = wl_result.get("confidence", "N/A")
        result.wl_needs_review = wl_result.get("needs_manual_review", "No")
        result.wl_reasons = [r.get("vector", "") for r in wl_result.get("flag_reasons", [])]
        result.wl_comment = wl_result.get("comment", "")
        
        if wl_result.get("error"):
            result.wl_error = wl_result["error"]
    except Exception as e:
        result.wl_error = str(e)
    
    # Determine overall QA verdict
    result.qa_verdict = determine_qa_verdict(result)
    
    return result


def determine_qa_verdict(result: AppQAResult) -> str:
    """Determine overall QA verdict based on all analyses."""
    if not result.download_success:
        return "DOWNLOAD_ERROR"
    
    # Play Integrity issues are most critical
    if result.pi_verdict == "FAIL":
        result.qa_notes.append(f"Play Integrity FAIL: {', '.join(result.pi_fail_reasons)}")
        return "FAIL"
    
    if result.pi_verdict == "WARNING":
        result.qa_notes.append(f"Play Integrity WARNING: {', '.join(result.pi_warning_reasons)}")
    
    if result.pi_verdict == "INCONCLUSIVE":
        result.qa_notes.append("Play Integrity analysis was inconclusive")
    
    # Wake Lock detection
    if result.wl_detected and result.wl_confidence in ("high", "medium"):
        result.qa_notes.append(f"Wake Lock detected ({result.wl_confidence} confidence)")
    
    if result.wl_needs_review == "Yes":
        result.qa_notes.append("Wake Lock requires manual review")
    
    # Determine final verdict
    if result.pi_verdict == "FAIL":
        return "FAIL"
    elif result.pi_verdict == "WARNING" or result.pi_verdict == "INCONCLUSIVE":
        return "WARNING"
    elif result.pi_verdict == "PASS":
        return "PASS"
    else:
        return "ERROR"


def print_result_card(result: AppQAResult, index: int):
    """Print a formatted result card for a single app."""
    print(f"\n{'='*70}")
    print(f"  [{index}] {result.filename}")
    print(f"{'='*70}")
    
    if not result.download_success:
        print(f"  ❌ Download Failed: {result.download_error}")
        return
    
    print(f"  Package:    {result.package_name}")
    print(f"  App Name:   {result.app_name}")
    print(f"  File Size:  {result.file_size_mb} MB ({result.file_type.upper()})")
    print()
    
    # Play Integrity
    pi_icons = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "INCONCLUSIVE": "⚙️", "ERROR": "❓"}
    print(f"  Play Integrity: {pi_icons.get(result.pi_verdict, '❓')} {result.pi_verdict}")
    if result.pi_fail_reasons:
        print(f"    FAIL reasons: {', '.join(result.pi_fail_reasons)}")
    if result.pi_warning_reasons:
        print(f"    WARNING reasons: {', '.join(result.pi_warning_reasons)}")
    if result.pi_error:
        print(f"    Error: {result.pi_error}")
    
    # Wake Lock
    wl_icon = "🔆" if result.wl_detected else "🌙"
    print(f"  Wake Lock:      {wl_icon} {'Detected' if result.wl_detected else 'Not Detected'} ({result.wl_confidence})")
    if result.wl_reasons:
        print(f"    Vectors: {', '.join(result.wl_reasons[:3])}")
    if result.wl_needs_review == "Yes":
        print(f"    ⚠️ Manual review required")
    
    # Overall verdict
    qa_icons = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "ERROR": "❓", "DOWNLOAD_ERROR": "⬇️"}
    print()
    print(f"  QA Verdict: {qa_icons.get(result.qa_verdict, '❓')} {result.qa_verdict}")
    if result.qa_notes:
        for note in result.qa_notes:
            print(f"    • {note}")


def print_summary_table(results: list[AppQAResult]):
    """Print a summary table of all results."""
    print(f"\n{'='*80}")
    print("  QA RESULTS SUMMARY")
    print(f"{'='*80}\n")
    
    # Count verdicts
    verdicts = {}
    for r in results:
        verdicts[r.qa_verdict] = verdicts.get(r.qa_verdict, 0) + 1
    
    total = len(results)
    print(f"  Total Apps: {total}")
    for verdict, count in sorted(verdicts.items()):
        icon = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "ERROR": "❓", "DOWNLOAD_ERROR": "⬇️"}.get(verdict, "?")
        print(f"    {icon} {verdict}: {count}")
    
    print(f"\n  {'─'*76}")
    print(f"  {'#':<4} {'Package':<40} {'PI':<8} {'WL':<6} {'QA':<10}")
    print(f"  {'─'*76}")
    
    for i, r in enumerate(results, 1):
        pkg = (r.package_name or r.filename)[:38]
        pi = r.pi_verdict[:6] if r.pi_verdict else "ERR"
        wl = "Yes" if r.wl_detected else "No"
        qa = r.qa_verdict[:8]
        print(f"  {i:<4} {pkg:<40} {pi:<8} {wl:<6} {qa:<10}")
    
    print(f"  {'─'*76}\n")


def export_csv(results: list[AppQAResult], output_path: str):
    """Export results to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "URL", "Filename", "File Type", "File Size (MB)",
            "Package Name", "App Name",
            "Play Integrity Verdict", "PI Fail Reasons", "PI Warning Reasons",
            "Wake Lock Detected", "WL Confidence", "WL Needs Review", "WL Vectors",
            "QA Verdict", "QA Notes"
        ])
        
        for r in results:
            writer.writerow([
                r.url,
                r.filename,
                r.file_type,
                r.file_size_mb or "",
                r.package_name or "",
                r.app_name or "",
                r.pi_verdict,
                "; ".join(r.pi_fail_reasons),
                "; ".join(r.pi_warning_reasons),
                "Yes" if r.wl_detected else "No",
                r.wl_confidence,
                r.wl_needs_review,
                "; ".join(r.wl_reasons),
                r.qa_verdict,
                "; ".join(r.qa_notes)
            ])
    
    print(f"  Results exported to: {output_path}")


def export_json(results: list[AppQAResult], output_path: str):
    """Export results to JSON."""
    data = []
    for r in results:
        data.append({
            "url": r.url,
            "filename": r.filename,
            "file_type": r.file_type,
            "file_size_mb": r.file_size_mb,
            "package_name": r.package_name,
            "app_name": r.app_name,
            "play_integrity": {
                "verdict": r.pi_verdict,
                "fail_reasons": r.pi_fail_reasons,
                "warning_reasons": r.pi_warning_reasons,
                "error": r.pi_error,
            },
            "wake_lock": {
                "detected": r.wl_detected,
                "confidence": r.wl_confidence,
                "needs_review": r.wl_needs_review,
                "vectors": r.wl_reasons,
                "comment": r.wl_comment,
                "error": r.wl_error,
            },
            "qa_verdict": r.qa_verdict,
            "qa_notes": r.qa_notes,
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Results exported to: {output_path}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python batch_app_qa.py <url1> [url2] ... [--csv output.csv] [--json output.json]")
        print("       python batch_app_qa.py --file urls.txt [--csv output.csv] [--json output.json]")
        sys.exit(1)
    
    # Parse arguments
    urls = []
    csv_output = None
    json_output = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--file" and i + 1 < len(sys.argv):
            with open(sys.argv[i + 1], 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        urls.append(line)
            i += 2
        elif arg == "--csv" and i + 1 < len(sys.argv):
            csv_output = sys.argv[i + 1]
            i += 2
        elif arg == "--json" and i + 1 < len(sys.argv):
            json_output = sys.argv[i + 1]
            i += 2
        elif arg.startswith("http"):
            urls.append(arg)
            i += 1
        else:
            i += 1
    
    if not urls:
        print("No URLs provided.")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"  Batch App QA Analysis")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Apps to analyze: {len(urls)}")
    print(f"{'='*70}\n")
    
    results: list[AppQAResult] = []
    
    # Create temporary working directory
    work_base = tempfile.mkdtemp(prefix="app_qa_")
    
    try:
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Processing: {get_filename_from_url(url)}...")
            
            # Create per-app work directory
            work_dir = os.path.join(work_base, f"app_{i}")
            os.makedirs(work_dir, exist_ok=True)
            
            try:
                result = analyze_app(url, work_dir)
                results.append(result)
                print_result_card(result, i)
            except Exception as e:
                print(f"  ❌ Error analyzing app: {e}")
                results.append(AppQAResult(
                    url=url,
                    filename=get_filename_from_url(url),
                    file_type="apk",
                    qa_verdict="ERROR",
                    qa_notes=[f"Analysis error: {str(e)}"]
                ))
            
            # Clean up to save space
            shutil.rmtree(work_dir, ignore_errors=True)
            
            # Small delay between apps
            if i < len(urls):
                time.sleep(0.5)
        
        # Print summary
        print_summary_table(results)
        
        # Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if csv_output:
            export_csv(results, csv_output)
        else:
            export_csv(results, f"/workspace/reports/qa_results_{timestamp}.csv")
        
        if json_output:
            export_json(results, json_output)
        else:
            export_json(results, f"/workspace/reports/qa_results_{timestamp}.json")
        
    finally:
        # Clean up
        shutil.rmtree(work_base, ignore_errors=True)
    
    # Return exit code based on results
    fail_count = sum(1 for r in results if r.qa_verdict == "FAIL")
    if fail_count > 0:
        print(f"\n⚠️  {fail_count} app(s) FAILED QA checks.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
