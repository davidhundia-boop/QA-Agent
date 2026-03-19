#!/usr/bin/env python3
"""
Batch QA Analysis Script for APK files.
Runs Play Integrity and Wake Lock analysis on all APKs.
"""

import json
import os
import sys
import csv
import zipfile
import tempfile
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, '/workspace')

from play_integrity_analyzer import PlayIntegrityAnalyzer
from wake_lock_analyzer import analyze_apk as analyze_wake_lock

def extract_base_apk_from_apks(apks_path):
    """Extract the base.apk from an .apks bundle for analysis."""
    try:
        with zipfile.ZipFile(apks_path, 'r') as zf:
            for name in zf.namelist():
                if 'base' in name.lower() and name.endswith('.apk'):
                    tmp_dir = tempfile.mkdtemp()
                    extracted_path = zf.extract(name, tmp_dir)
                    return extracted_path
            for name in zf.namelist():
                if name.endswith('.apk'):
                    tmp_dir = tempfile.mkdtemp()
                    extracted_path = zf.extract(name, tmp_dir)
                    return extracted_path
    except Exception as e:
        print(f"Error extracting {apks_path}: {e}")
    return None

def analyze_single_apk(apk_path):
    """Run all analyses on a single APK file."""
    filename = os.path.basename(apk_path)
    result = {
        "filename": filename,
        "filepath": apk_path,
        "analyzed_at": datetime.now().isoformat(),
        "play_integrity": None,
        "wake_lock": None,
        "errors": []
    }
    
    analysis_path = apk_path
    temp_extracted = None
    
    if apk_path.endswith('.apks'):
        temp_extracted = extract_base_apk_from_apks(apk_path)
        if temp_extracted:
            analysis_path = temp_extracted
        else:
            result["errors"].append("Failed to extract base APK from .apks bundle")
            return result
    
    try:
        print(f"[Play Integrity] Analyzing {filename}...")
        analyzer = PlayIntegrityAnalyzer(analysis_path)
        analyzer._extract_apk_data()
        analyzer._check_pairip()
        analyzer._check_play_integrity()
        analyzer._check_legacy_licensing()
        analyzer._determine_verdict()
        
        result["play_integrity"] = {
            "package": analyzer.package_name,
            "app_name": analyzer.app_name,
            "verdict": analyzer._determine_verdict_silent(),
            "pairip_detected": len(analyzer.pairip_evidence) > 0,
            "play_integrity_api": analyzer.play_integrity_detected,
            "legacy_licensing": len(analyzer.lvl_evidence) > 0,
            "fail_reasons": [r["name"] for r in analyzer.results["fail"]],
            "warning_reasons": [r["name"] for r in analyzer.results["warning"]],
            "dex_strings_count": len(analyzer.dex_strings),
        }
    except Exception as e:
        result["errors"].append(f"Play Integrity analysis error: {str(e)}")
        print(f"[ERROR] Play Integrity failed for {filename}: {e}")
    
    try:
        print(f"[Wake Lock] Analyzing {filename}...")
        wake_result = analyze_wake_lock(analysis_path)
        result["wake_lock"] = {
            "package": wake_result.get("package"),
            "main_activity": wake_result.get("main_activity"),
            "wake_lock_detected": wake_result.get("wake_lock_detected", False),
            "confidence": wake_result.get("confidence"),
            "needs_manual_review": wake_result.get("needs_manual_review"),
            "flag_reasons_count": len(wake_result.get("flag_reasons", [])),
            "flag_reasons_summary": [r.get("vector") for r in wake_result.get("flag_reasons", [])[:5]],
            "comment": wake_result.get("comment", "")[:500],
        }
    except Exception as e:
        result["errors"].append(f"Wake Lock analysis error: {str(e)}")
        print(f"[ERROR] Wake Lock failed for {filename}: {e}")
    
    if temp_extracted:
        try:
            import shutil
            shutil.rmtree(os.path.dirname(temp_extracted))
        except:
            pass
    
    return result

def generate_csv_report(results, output_path):
    """Generate CSV report from analysis results."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Filename",
            "Package Name",
            "App Name",
            "Play Integrity Verdict",
            "Pairip (Auto Protect)",
            "Play Integrity API",
            "Legacy Licensing (LVL)",
            "Play Integrity Issues",
            "Wake Lock Detected",
            "Wake Lock Confidence",
            "Wake Lock Manual Review",
            "Wake Lock Reasons",
            "Errors"
        ])
        
        for r in results:
            pi = r.get("play_integrity") or {}
            wl = r.get("wake_lock") or {}
            
            pi_issues = pi.get("fail_reasons", []) + pi.get("warning_reasons", [])
            
            writer.writerow([
                r.get("filename", ""),
                pi.get("package", wl.get("package", "")),
                pi.get("app_name", ""),
                pi.get("verdict", "N/A"),
                "YES" if pi.get("pairip_detected") else "NO",
                "YES" if pi.get("play_integrity_api") else "NO",
                "YES" if pi.get("legacy_licensing") else "NO",
                "; ".join(pi_issues) if pi_issues else "None",
                "YES" if wl.get("wake_lock_detected") else "NO",
                wl.get("confidence", "N/A"),
                wl.get("needs_manual_review", "N/A"),
                "; ".join(wl.get("flag_reasons_summary", [])[:3]) if wl.get("flag_reasons_summary") else "None",
                "; ".join(r.get("errors", [])) if r.get("errors") else ""
            ])

def main():
    apk_dir = os.path.dirname(os.path.abspath(__file__))
    
    apk_files = []
    for f in os.listdir(apk_dir):
        if f.endswith('.apk') or f.endswith('.apks'):
            apk_files.append(os.path.join(apk_dir, f))
    
    apk_files.sort()
    
    print(f"\n{'='*70}")
    print(f"  APK Batch QA Analysis")
    print(f"  Total APKs: {len(apk_files)}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    results = []
    for i, apk_path in enumerate(apk_files, 1):
        print(f"\n[{i}/{len(apk_files)}] Processing {os.path.basename(apk_path)}...")
        result = analyze_single_apk(apk_path)
        results.append(result)
        
        pi = result.get("play_integrity") or {}
        wl = result.get("wake_lock") or {}
        print(f"  Package: {pi.get('package', wl.get('package', 'unknown'))}")
        print(f"  Play Integrity: {pi.get('verdict', 'N/A')}")
        print(f"  Wake Lock: {'YES' if wl.get('wake_lock_detected') else 'NO'} (confidence: {wl.get('confidence', 'N/A')})")
        if result.get("errors"):
            print(f"  Errors: {len(result['errors'])}")
    
    report_dir = os.path.join(apk_dir, "qa_reports")
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    json_path = os.path.join(report_dir, f"qa_report_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    csv_path = os.path.join(report_dir, f"qa_report_{timestamp}.csv")
    generate_csv_report(results, csv_path)
    
    pi_fail = sum(1 for r in results if r.get("play_integrity", {}).get("verdict") == "FAIL")
    pi_warn = sum(1 for r in results if r.get("play_integrity", {}).get("verdict") == "WARNING")
    pi_pass = sum(1 for r in results if r.get("play_integrity", {}).get("verdict") == "PASS")
    pi_inc = sum(1 for r in results if r.get("play_integrity", {}).get("verdict") == "INCONCLUSIVE")
    
    wl_yes = sum(1 for r in results if r.get("wake_lock", {}).get("wake_lock_detected"))
    wl_no = sum(1 for r in results if r.get("wake_lock") and not r.get("wake_lock", {}).get("wake_lock_detected"))
    
    errors = sum(len(r.get("errors", [])) for r in results)
    
    print(f"\n{'='*70}")
    print(f"  BATCH ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"\n  Play Integrity Results:")
    print(f"    FAIL:        {pi_fail}")
    print(f"    WARNING:     {pi_warn}")
    print(f"    PASS:        {pi_pass}")
    print(f"    INCONCLUSIVE:{pi_inc}")
    print(f"\n  Wake Lock Results:")
    print(f"    Detected:    {wl_yes}")
    print(f"    Not Detected:{wl_no}")
    print(f"\n  Errors: {errors}")
    print(f"\n  Reports saved to:")
    print(f"    JSON: {json_path}")
    print(f"    CSV:  {csv_path}")
    print(f"{'='*70}\n")
    
    return results

if __name__ == "__main__":
    main()
