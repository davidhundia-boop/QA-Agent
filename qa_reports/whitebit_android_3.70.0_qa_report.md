# QA Report: WhiteBIT Android App

**Date:** 2026-03-18  
**Analyst:** Automated QA System  
**Source:** https://whitelabel-cdn-prod.digitalturbine.com/files/26b417db-95ee-4530-91ed-baac8a75cab7.apks

---

## App Information

| Property | Value |
|----------|-------|
| **Package Name** | com.whitebit.android |
| **App Name** | WhiteBIT – buy & sell bitcoin |
| **Version Name** | 3.70.0 |
| **Version Code** | 30000393 |
| **Min SDK** | 24 (Android 7.0) |
| **Target SDK** | 36 |
| **Developer** | WhiteBit (whitebit.com) |
| **Contact** | info@whitebit.com |

---

## Overall QA Status

| Check | Status | Details |
|-------|--------|---------|
| Wake Lock Analysis | ⚠️ MEDIUM | Wake lock patterns detected in secondary screens |
| Play Integrity | ⚠️ WARNING | Play Integrity API detected - manual verification needed |
| Legal Compliance | ⚠️ WARNING | Terms & Conditions not found |

---

## 1. Wake Lock Analysis

**Result:** ⚠️ MEDIUM CONFIDENCE - Wake lock detected

### Findings

| Vector | Class | Confidence | Notes |
|--------|-------|------------|-------|
| `Window.addFlags(FLAG_KEEP_SCREEN_ON)` | `com.brentvatne.exoplayer.FullScreenPlayerView$KeepScreenOnUpdater` | Medium | Screen hold found in secondary activity - may only apply to specific app screens (video player), not the main experience |
| `keepScreenOn=true` (AXML) | `res/layout/sns_fragment_video_ident.xml` | Medium | Layout attribute for video identification screen |

### Assessment

The wake lock patterns are associated with video playback functionality (ExoPlayer full-screen view) and video identification screens, which is **expected and acceptable behavior**. The app is not holding wake locks on the main experience screens.

**Manual Review Required:** No

---

## 2. Play Integrity Analysis

**Result:** ⚠️ WARNING - Manual verification required

### Findings

The app uses **Play Integrity API** with 6 indicators detected:
- `com.google.android.play.core.integrity` package references
- `IntegrityTokenRequest` / `IntegrityTokenResponse` classes
- `StandardIntegrityManager` usage
- `IntegrityServiceException` handling

### Action Required

**Cannot determine statically whether Digital Turbine installs are permitted** — verdict handling is server-side.

**Recommendation:** Confirm with the WhiteBIT developer team that `KNOWN_` installers (including Digital Turbine) are allowed through their Play Integrity configuration.

### Additional Checks

| Check | Status |
|-------|--------|
| pairip / Auto Protect | ✅ Not detected |
| Legacy Play Licensing (LVL) | ✅ Not detected |

---

## 3. Legal Compliance

**Result:** ⚠️ WARNING

| Requirement | Status | Details |
|-------------|--------|---------|
| Privacy Policy | ✅ PASS | Available on Play Store: https://whitebit.com/privacy-policy |
| Terms & Conditions | ❌ NOT FOUND | Could not verify (website returns 403) |
| Data Safety | ✅ COMPLETE | Properly disclosed on Play Store |

### Data Safety Summary

**Data Collected:**
- Device or other IDs
- Personal info (Name, Email address, User IDs, Address, Phone number)
- App info and performance (Crash logs, Diagnostics)

**Data Shared:**
- Device or other IDs
- Personal info (Name, User IDs, Address, Phone number)

**Security Practices:**
- ✅ Data is encrypted in transit
- ✅ Users can request data deletion

### Notes

The developer website (https://whitebit.com/) returns HTTP 403 Forbidden when accessed programmatically, preventing automated Terms & Conditions verification. The Privacy Policy link from Play Store is valid and accessible.

---

## Summary & Recommendations

### Pre-Installation Checklist

- [ ] **Play Integrity Verification**: Contact WhiteBIT to confirm Digital Turbine is in their allowed installers list
- [ ] **Terms & Conditions**: Manually verify T&C availability at https://whitebit.com/terms or similar
- [ ] **Wake Lock**: No action needed - expected behavior for video playback

### Risk Assessment

| Category | Risk Level |
|----------|------------|
| Technical (Wake Lock) | 🟢 Low |
| Installation Blocking (Play Integrity) | 🟡 Medium - Requires verification |
| Legal Compliance | 🟡 Medium - T&C verification pending |

---

## Raw Analysis Data

### Wake Lock Analysis JSON

```json
{
  "apk_name": "base.apk",
  "package": "com.whitebit.android",
  "main_activity": "com.whitebit.whitebitu.MainActivityDefault",
  "wake_lock_detected": true,
  "confidence": "medium",
  "needs_manual_review": "No",
  "flag_reasons": [
    {
      "vector": "Window.addFlags(FLAG_KEEP_SCREEN_ON)",
      "found_in_class": "com.brentvatne.exoplayer.FullScreenPlayerView$KeepScreenOnUpdater",
      "found_in_method": "run",
      "tier": 3,
      "confidence": "medium"
    },
    {
      "vector": "AXML keepScreenOn=true in res/layout/sns_fragment_video_ident.xml",
      "found_in_class": "res/layout/sns_fragment_video_ident.xml",
      "tier": 3,
      "confidence": "medium"
    }
  ],
  "classes_scanned": 1678,
  "total_classes_in_apk": 70618
}
```

### Play Integrity Analysis JSON

```json
{
  "apk": "base.apk",
  "package": "com.whitebit.android",
  "app_name": "WhiteBIT",
  "verdict": "WARNING",
  "fail_count": 0,
  "warning_count": 1,
  "play_integrity_detected": true,
  "details": {
    "warning": [
      {
        "id": "play_integrity_api",
        "name": "Play Integrity API",
        "evidence_count": 6,
        "description": "App uses Play Integrity API. Cannot determine statically whether DT installs are permitted -- verdict handling is server-side."
      }
    ]
  },
  "analyzed_at": "2026-03-18T20:12:57.748385"
}
```

---

*Report generated by automated QA toolkit*
