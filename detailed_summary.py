#!/usr/bin/env python3
"""Generate detailed wake lock analysis summary."""

import json

results = []
with open('/workspace/wake_lock_results.json', 'r') as f:
    content = f.read()
    
# Parse multiple JSON objects
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

print("=" * 80)
print("WAKE LOCK ANALYSIS SUMMARY")
print("=" * 80)
print()

# Basic counts
total = len(results)
wake_lock_true = [r for r in results if r.get('wake_lock_detected', False)]
wake_lock_false = [r for r in results if not r.get('wake_lock_detected', False)]

print(f"1. TOTAL APKs ANALYZED: {total}")
print()

print("2. COUNT BY DETECTION STATUS:")
print(f"   wake_lock_detected = true:  {len(wake_lock_true)} APKs")
print(f"   wake_lock_detected = false: {len(wake_lock_false)} APKs")
print()

# Confidence level counts
conf_map = {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
for r in results:
    conf = r.get('confidence', 'none')
    conf_map[conf] = conf_map.get(conf, 0) + 1

print("3. COUNT BY CONFIDENCE LEVEL:")
print(f"   High:   {conf_map.get('high', 0)} APKs")
print(f"   Medium: {conf_map.get('medium', 0)} APKs")
print(f"   Low:    {conf_map.get('low', 0)} APKs")  
print(f"   None:   {conf_map.get('none', 0)} APKs")
print()

# Count by best tier among flagged APKs
tier_distribution = {}
for r in wake_lock_true:
    reasons = r.get('flag_reasons', [])
    if reasons:
        best_tier = min(f.get('tier', 99) for f in reasons)
        tier_distribution[best_tier] = tier_distribution.get(best_tier, 0) + 1

print("4. FLAGGED APKs BY BEST TIER:")
tier_desc = {
    1: "Tier 1 (High confidence - Main activity screen holds)",
    2: "Tier 2 (High confidence - Game engine runtime)",
    3: "Tier 3 (Medium confidence - Secondary activities, PowerManager)",
    4: "Tier 4 (Low confidence - Unity sleepTimeout, needs verification)",
    5: "Tier 5 (None - Ad SDK only)"
}
for tier in sorted(tier_distribution.keys()):
    print(f"   {tier_desc.get(tier, f'Tier {tier}')}: {tier_distribution[tier]} APKs")
print()

print("-" * 80)
print("5. APKs WITH wake_lock_detected = true")
print("-" * 80)
print()

# Sort by tier (best first)
def get_best_tier(r):
    reasons = r.get('flag_reasons', [])
    if not reasons:
        return 99
    return min(f.get('tier', 99) for f in reasons)

for r in sorted(wake_lock_true, key=lambda x: (get_best_tier(x), x.get('package', ''))):
    pkg = r.get('package', 'unknown')
    conf = r.get('confidence', 'unknown')
    apk_name = r.get('apk_name', 'unknown')
    reasons = r.get('flag_reasons', [])
    best_tier = get_best_tier(r)
    
    # Get primary reason (first one with best tier)
    primary_reasons = [f for f in reasons if f.get('tier') == best_tier]
    primary = primary_reasons[0] if primary_reasons else (reasons[0] if reasons else None)
    
    print(f"Package: {pkg}")
    print(f"  APK File: {apk_name}")
    print(f"  Confidence: {conf.upper()}")
    print(f"  Best Tier: {best_tier}")
    
    if primary:
        print(f"  Primary Detection: {primary.get('vector', 'N/A')}")
        print(f"    Found in: {primary.get('found_in_class', 'N/A')}.{primary.get('found_in_method', 'N/A')}()")
        if primary.get('note'):
            print(f"    Note: {primary.get('note')[:100]}...")
    
    # Show if there are additional detections
    if len(reasons) > 1:
        print(f"  Additional detections: {len(reasons) - 1} more")
        other_tiers = set(f.get('tier') for f in reasons) - {best_tier}
        if other_tiers:
            print(f"    (including tiers: {sorted(other_tiers)})")
    
    if r.get('needs_manual_review') == 'Yes':
        print(f"  ⚠️  MANUAL REVIEW REQUIRED")
    print()

# Manual review section
needs_review = [r for r in results if r.get('needs_manual_review') == 'Yes']
print("-" * 80)
print(f"6. APKs NEEDING MANUAL REVIEW: {len(needs_review)}")
print("-" * 80)
if needs_review:
    for r in needs_review:
        print(f"\nPackage: {r.get('package', 'unknown')}")
        print(f"  APK: {r.get('apk_name', 'unknown')}")
        print(f"  Instructions: {r.get('manual_review_instructions', 'N/A')}")
else:
    print("None")
print()

# Errors
errors = [r for r in results if 'error' in r]
print("-" * 80)
print(f"7. ERRORS ENCOUNTERED: {len(errors)}")
print("-" * 80)
if errors:
    for r in errors:
        print(f"  {r.get('apk_name', 'unknown')}: {r.get('error', 'unknown')}")
else:
    print("None")
print()

# Processing stats
total_time = sum(r.get('time_taken_seconds', 0) for r in results)
avg_time = total_time / len(results) if results else 0
print("-" * 80)
print("8. PROCESSING STATISTICS")
print("-" * 80)
print(f"  Total processing time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
print(f"  Average per APK: {avg_time:.2f} seconds")
print()

# Summary table for easy reference
print("=" * 80)
print("QUICK REFERENCE TABLE: FLAGGED APKs")
print("=" * 80)
print(f"{'Package':<55} {'Tier':<6} {'Confidence':<10}")
print("-" * 80)
for r in sorted(wake_lock_true, key=lambda x: (get_best_tier(x), x.get('package', ''))):
    pkg = r.get('package', 'unknown')[:54]
    best_tier = get_best_tier(r)
    conf = r.get('confidence', 'unknown')
    print(f"{pkg:<55} {best_tier:<6} {conf:<10}")
