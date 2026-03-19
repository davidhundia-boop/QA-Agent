#!/usr/bin/env python3
"""Parse wake lock analysis results and generate summary."""

import json
import sys

results = []
with open('/workspace/wake_lock_results.json', 'r') as f:
    content = f.read()
    
# The output is multiple JSON objects, not a JSON array
# Split by '}' and parse each one
depth = 0
current = ""
for char in content:
    current += char
    if char == '{':
        depth += 1
    elif char == '}':
        depth -= 1
        if depth == 0:
            try:
                obj = json.loads(current.strip())
                results.append(obj)
            except json.JSONDecodeError:
                pass
            current = ""

print(f"Total APKs analyzed: {len(results)}")
print()

# Count by detection status
wake_lock_true = [r for r in results if r.get('wake_lock_detected', False)]
wake_lock_false = [r for r in results if not r.get('wake_lock_detected', False)]
errors = [r for r in results if 'error' in r]

print("=== Detection Status Summary ===")
print(f"wake_lock_detected = true:  {len(wake_lock_true)}")
print(f"wake_lock_detected = false: {len(wake_lock_false)}")
print(f"Errors encountered:         {len(errors)}")
print()

# Count by confidence level
confidence_counts = {}
for r in results:
    conf = r.get('confidence', 'unknown')
    confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

print("=== Confidence Level Distribution ===")
for conf, count in sorted(confidence_counts.items()):
    print(f"  {conf}: {count}")
print()

# Count manual review needed
needs_review = [r for r in results if r.get('needs_manual_review') == 'Yes']
print(f"=== Manual Review Required: {len(needs_review)} APKs ===")
print()

# List APKs with wake_lock_detected=true
print("=== APKs with wake_lock_detected = true ===")
print()
for r in sorted(wake_lock_true, key=lambda x: x.get('confidence', 'z')):
    pkg = r.get('package', 'unknown')
    conf = r.get('confidence', 'unknown')
    apk_name = r.get('apk_name', 'unknown')
    
    # Get primary detection reason
    reasons = r.get('flag_reasons', [])
    primary_reason = reasons[0]['vector'] if reasons else 'N/A'
    tier = reasons[0].get('tier', 'N/A') if reasons else 'N/A'
    
    print(f"Package: {pkg}")
    print(f"  APK: {apk_name}")
    print(f"  Confidence: {conf} (Tier {tier})")
    print(f"  Primary Detection: {primary_reason}")
    if r.get('needs_manual_review') == 'Yes':
        print(f"  ⚠️  Manual review required")
    print()

# List APKs needing manual review
print("=== APKs Needing Manual Review ===")
print()
for r in needs_review:
    pkg = r.get('package', 'unknown')
    apk_name = r.get('apk_name', 'unknown')
    instructions = r.get('manual_review_instructions', 'N/A')
    print(f"Package: {pkg}")
    print(f"  APK: {apk_name}")
    print(f"  Instructions: {instructions}")
    print()

# List errors if any
if errors:
    print("=== Errors Encountered ===")
    for r in errors:
        print(f"  {r.get('apk_name', 'unknown')}: {r.get('error', 'unknown error')}")
    print()

# Generate more detailed tier breakdown
print("=== Detection Tier Breakdown (for flagged APKs) ===")
tier_counts = {}
for r in wake_lock_true:
    for reason in r.get('flag_reasons', []):
        tier = reason.get('tier', 'unknown')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
for tier, count in sorted(tier_counts.items()):
    tier_labels = {
        1: "High - Main activity chain screen holds",
        2: "High - Game engine runtime wake locks",
        3: "Medium - Secondary activities, PowerManager",
        4: "Low - Unity sleepTimeout (needs verification)",
        5: "None - Ad SDK only"
    }
    label = tier_labels.get(tier, f"Unknown tier {tier}")
    print(f"  Tier {tier} ({label}): {count} detections")
