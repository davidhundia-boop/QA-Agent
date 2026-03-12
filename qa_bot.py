#!/usr/bin/env python3
"""
QA Bot - Combined Android App Quality Assurance Report

Runs all three analyzers and produces a unified markdown report:
- Play Integrity Analyzer
- Legal Compliance Checker
- Wake Lock Analyzer

Usage:
    python qa_bot.py <apk_path> [--package PACKAGE] [--verbose]
    python qa_bot.py --package com.example.app [--verbose]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional

# Ensure UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower().replace('-', '') != 'utf8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


@dataclass
class CheckResult:
    name: str
    status: str  # PASS, FAIL, WARNING, NEEDS_MANUAL_REVIEW, SKIPPED, ERROR
    details: str
    raw_output: Optional[dict] = None


def get_status_icon(status: str) -> str:
    icons = {
        "PASS": "✅",
        "FAIL": "❌",
        "WARNING": "⚠️",
        "NEEDS_MANUAL_REVIEW": "⚠️",
        "SKIPPED": "⏭️",
        "ERROR": "❌",
        "INCONCLUSIVE": "❓",
    }
    return icons.get(status, "❓")


def format_status(status: str) -> str:
    if status == "PASS":
        return "✅ **PASS**"
    elif status == "FAIL":
        return "❌ **FAIL**"
    elif status in ("WARNING", "NEEDS_MANUAL_REVIEW"):
        return "⚠️ **NEEDS MANUAL REVIEW**"
    elif status == "SKIPPED":
        return "⏭️ **SKIPPED**"
    elif status == "INCONCLUSIVE":
        return "❓ **INCONCLUSIVE**"
    else:
        return f"❌ **{status}**"


def run_play_integrity(apk_path: str, verbose: bool = False) -> CheckResult:
    """Run the Play Integrity Analyzer."""
    if not os.path.isfile(apk_path):
        return CheckResult(
            name="Play Integrity",
            status="SKIPPED",
            details="APK file not provided",
        )

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "play_integrity_analyzer.py")
        
        result = subprocess.run(
            [sys.executable, script_path, apk_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        # Parse the JSON output from the analyzer
        lines = result.stdout.strip().split('\n')
        json_output = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                try:
                    json_output = json.loads('\n'.join(lines[i:]))
                    break
                except json.JSONDecodeError:
                    continue
        
        if json_output is None:
            # Try to extract verdict from text output
            if "VERDICT:" in result.stdout:
                if "[PASS]" in result.stdout:
                    return CheckResult(
                        name="Play Integrity",
                        status="PASS",
                        details="No blocking protections detected. Safe for DT preloads.",
                    )
                elif "[FAIL]" in result.stdout:
                    return CheckResult(
                        name="Play Integrity",
                        status="FAIL",
                        details="Blocking protections detected. Will break on DT preloads.",
                    )
                elif "[WARN]" in result.stdout:
                    return CheckResult(
                        name="Play Integrity",
                        status="WARNING",
                        details="Play Integrity API detected. Manual verification needed.",
                    )
            return CheckResult(
                name="Play Integrity",
                status="ERROR",
                details="Could not parse analyzer output",
            )
        
        verdict = json_output.get("verdict", "UNKNOWN")
        
        if verdict == "PASS":
            details = "No blocking protections detected. Safe for DT preloads."
        elif verdict == "FAIL":
            fail_items = json_output.get("details", {}).get("fail", [])
            reasons = [item.get("name", "") for item in fail_items]
            details = f"Blocking: {', '.join(reasons)}" if reasons else "Blocking protections detected."
        elif verdict == "WARNING":
            warn_items = json_output.get("details", {}).get("warning", [])
            reasons = [item.get("name", "") for item in warn_items]
            details = f"Detected: {', '.join(reasons)}. Manual verification needed."
        elif verdict == "INCONCLUSIVE":
            details = "Could not fully analyze. Manual testing required."
        else:
            details = "Unknown verdict"
        
        return CheckResult(
            name="Play Integrity",
            status=verdict,
            details=details,
            raw_output=json_output,
        )
        
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="Play Integrity",
            status="ERROR",
            details="Analysis timed out",
        )
    except Exception as e:
        return CheckResult(
            name="Play Integrity",
            status="ERROR",
            details=f"Error: {str(e)}",
        )


def run_legal_compliance(package_name: str, apk_path: Optional[str] = None, 
                         verbose: bool = False) -> CheckResult:
    """Run the Legal Compliance Checker."""
    if not package_name:
        return CheckResult(
            name="Legal Compliance",
            status="SKIPPED",
            details="Package name not provided",
        )

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "check_app_legal.py")
        
        cmd = [sys.executable, script_path, package_name, "--no-datasafety"]
        if verbose:
            cmd.append("--verbose")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        output = result.stdout
        
        # Parse the output to determine status
        pp_found = "Privacy Pol." in output and "✅" in output.split("Privacy Pol.")[1].split("\n")[0]
        tc_found = "Terms & Con." in output and "✅" in output.split("Terms & Con.")[1].split("\n")[0]
        
        # Look for the RATING line
        if "RATING: ✅ PASS" in output:
            return CheckResult(
                name="Legal Compliance",
                status="PASS",
                details="Privacy Policy & Terms verified",
            )
        elif "RATING: ⚠️ WARNING" in output or "RATING: ⚠" in output:
            missing = []
            if not pp_found:
                missing.append("Privacy Policy")
            if not tc_found:
                missing.append("Terms & Conditions")
            details = f"Missing: {', '.join(missing)}" if missing else "Partial compliance"
            return CheckResult(
                name="Legal Compliance",
                status="WARNING",
                details=details,
            )
        elif "RATING: ❌ FAIL" in output or "RATING:" in output:
            return CheckResult(
                name="Legal Compliance",
                status="FAIL",
                details="Privacy Policy and/or Terms not found",
            )
        elif "not found on Google Play Store" in output.lower():
            return CheckResult(
                name="Legal Compliance",
                status="WARNING",
                details="App not found on Play Store",
            )
        else:
            return CheckResult(
                name="Legal Compliance",
                status="ERROR",
                details="Could not determine compliance status",
            )
        
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="Legal Compliance",
            status="ERROR",
            details="Analysis timed out",
        )
    except Exception as e:
        return CheckResult(
            name="Legal Compliance",
            status="ERROR",
            details=f"Error: {str(e)}",
        )


def run_wake_lock(apk_path: str, verbose: bool = False) -> CheckResult:
    """Run the Wake Lock Analyzer."""
    if not os.path.isfile(apk_path):
        return CheckResult(
            name="Wake Lock",
            status="SKIPPED",
            details="APK file not provided",
        )

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "wake_lock_analyzer.py")
        
        result = subprocess.run(
            [sys.executable, script_path, apk_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        # Parse the JSON output
        try:
            json_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            return CheckResult(
                name="Wake Lock",
                status="ERROR",
                details="Could not parse analyzer output",
            )
        
        detected = json_output.get("wake_lock_detected", False)
        confidence = json_output.get("confidence", "unknown")
        needs_review = json_output.get("needs_manual_review", "No") == "Yes"
        tier = json_output.get("tier")
        
        if not detected:
            if tier == 5 or confidence == "none":
                return CheckResult(
                    name="Wake Lock",
                    status="PASS",
                    details="No wake lock detected (SDK-only references filtered)",
                    raw_output=json_output,
                )
            return CheckResult(
                name="Wake Lock",
                status="PASS",
                details="No wake lock detected",
                raw_output=json_output,
            )
        
        if needs_review:
            return CheckResult(
                name="Wake Lock",
                status="NEEDS_MANUAL_REVIEW",
                details=f"{confidence.capitalize()} confidence detection",
                raw_output=json_output,
            )
        
        if confidence == "high":
            return CheckResult(
                name="Wake Lock",
                status="FAIL",
                details="Wake lock detected with high confidence",
                raw_output=json_output,
            )
        elif confidence == "medium":
            return CheckResult(
                name="Wake Lock",
                status="WARNING",
                details="Wake lock detected with medium confidence",
                raw_output=json_output,
            )
        else:
            return CheckResult(
                name="Wake Lock",
                status="NEEDS_MANUAL_REVIEW",
                details=f"{confidence.capitalize()} confidence detection",
                raw_output=json_output,
            )
        
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="Wake Lock",
            status="ERROR",
            details="Analysis timed out",
        )
    except Exception as e:
        return CheckResult(
            name="Wake Lock",
            status="ERROR",
            details=f"Error: {str(e)}",
        )


def extract_package_from_apk(apk_path: str) -> Optional[str]:
    """Extract package name from APK using aapt2 or androguard."""
    for tool in ("aapt2", "aapt"):
        try:
            result = subprocess.run(
                [tool, "dump", "badging", apk_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import re
                match = re.search(r"name='([^']+)'", result.stdout)
                if match:
                    return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    # Fallback to androguard
    try:
        from androguard.core.apk import APK
        apk = APK(apk_path)
        return apk.get_package()
    except Exception:
        pass
    
    return None


def print_report(results: list[CheckResult], apk_name: str = "", package_name: str = ""):
    """Print the formatted QA report."""
    print("\n## QA Report")
    if apk_name:
        print(f"**APK:** {apk_name}")
    if package_name:
        print(f"**Package:** {package_name}")
    print()
    
    print("| Check | Result | Details |")
    print("|-------|--------|---------|")
    
    for result in results:
        status_str = format_status(result.status)
        print(f"| **{result.name}** | {status_str} | {result.details} |")
    
    print()
    
    # Overall summary
    statuses = [r.status for r in results]
    if "FAIL" in statuses:
        print("### ❌ Overall: FAIL")
        print("One or more checks failed. Review details above.")
    elif "ERROR" in statuses:
        print("### ❌ Overall: ERROR")
        print("One or more checks encountered errors.")
    elif "WARNING" in statuses or "NEEDS_MANUAL_REVIEW" in statuses:
        print("### ⚠️ Overall: NEEDS REVIEW")
        print("Some checks need manual verification.")
    elif all(s in ("PASS", "SKIPPED") for s in statuses):
        print("### ✅ Overall: PASS")
        print("All checks passed.")
    else:
        print("### ❓ Overall: INCONCLUSIVE")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="QA Bot - Combined Android App Quality Assurance Report",
    )
    parser.add_argument(
        "apk",
        nargs="?",
        help="Path to APK file",
    )
    parser.add_argument(
        "--package", "-p",
        help="Package name (auto-detected from APK if not provided)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--skip-integrity",
        action="store_true",
        help="Skip Play Integrity check",
    )
    parser.add_argument(
        "--skip-legal",
        action="store_true",
        help="Skip Legal Compliance check",
    )
    parser.add_argument(
        "--skip-wakelock",
        action="store_true",
        help="Skip Wake Lock check",
    )
    
    args = parser.parse_args()
    
    if not args.apk and not args.package:
        parser.error("Either APK path or --package is required")
    
    apk_path = args.apk or ""
    apk_name = os.path.basename(apk_path) if apk_path else ""
    package_name = args.package
    
    # Extract package name from APK if not provided
    if apk_path and not package_name:
        if args.verbose:
            print("Extracting package name from APK...")
        package_name = extract_package_from_apk(apk_path)
        if package_name and args.verbose:
            print(f"Package: {package_name}")
    
    results = []
    
    # Run Play Integrity check
    if not args.skip_integrity:
        if args.verbose:
            print("\n[1/3] Running Play Integrity Analyzer...")
        results.append(run_play_integrity(apk_path, args.verbose))
    
    # Run Legal Compliance check
    if not args.skip_legal:
        if args.verbose:
            print("\n[2/3] Running Legal Compliance Checker...")
        results.append(run_legal_compliance(package_name, apk_path, args.verbose))
    
    # Run Wake Lock check
    if not args.skip_wakelock:
        if args.verbose:
            print("\n[3/3] Running Wake Lock Analyzer...")
        results.append(run_wake_lock(apk_path, args.verbose))
    
    # Print the report
    print_report(results, apk_name, package_name)


if __name__ == "__main__":
    main()
