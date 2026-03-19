# New App QA Report

**App:** WhiteBIT – buy & sell bitcoin  
**Package:** `com.whitebit.android`  
**Developer:** WhiteBit  
**QA Date:** 2026-03-18  
**Source:** https://whitelabel-cdn-prod.digitalturbine.com/files/26b417db-95ee-4530-91ed-baac8a75cab7.apks

---

## Summary

| Check | Result | Confidence |
|-------|--------|------------|
| Play Integrity | ⚠️ WARNING | Needs manual verification |
| Wake Lock | ⚠️ DETECTED | Medium confidence |
| Privacy Policy | ✅ FOUND | Play Store |
| Terms & Conditions | ❌ NOT FOUND | - |
| Data Safety | ✅ COMPLETE | - |

**Overall Status:** ⚠️ **WARNING** - Manual verification required before DT preload approval

---

## 1. Play Integrity Analysis

**Verdict:** ⚠️ WARNING

### Findings

The app uses **Play Integrity API**, which means:
- Cannot determine statically whether DT installs are permitted
- Verdict handling is server-side
- **Requires one-time manual verification**: confirm with the developer that KNOWN_ installers (including Digital Turbine) are allowed through

### Evidence (6 indicators)

| Type | Indicator | Location |
|------|-----------|----------|
| DEX | `com.google.android.play.core.integrity` | `IRequestDialogCallback` |
| DEX | `com/google/android/play/core/integrity` | Various classes |
| DEX | `IntegrityTokenRequest` | `StandardIntegrityManager$PrepareIntegrityTokenRequest` |
| DEX | `IntegrityTokenResponse` | `IntegrityTokenResponse` |
| DEX | `StandardIntegrityManager` | `PrepareIntegrityTokenRequest` |
| DEX | `IntegrityServiceException` | Core integrity classes |

### No Blocking Issues Found

- ✅ No pairip / Auto Protect detected
- ✅ No Legacy Play Licensing (LVL) detected

---

## 2. Wake Lock Analysis

**Verdict:** ⚠️ DETECTED (Medium Confidence)

### Findings

Wake lock patterns detected in the app. These may only apply to specific app screens (video playback), not the main experience.

| Vector | Class | Method | Tier | Notes |
|--------|-------|--------|------|-------|
| `Window.addFlags(FLAG_KEEP_SCREEN_ON)` | `com.brentvatne.exoplayer.FullScreenPlayerView$KeepScreenOnUpdater` | `run()` | 3 | Exoplayer video fullscreen - expected behavior |
| AXML `keepScreenOn=true` | `res/layout/sns_fragment_video_ident.xml` | N/A | 3 | Video identification layout |

### Analysis

- Both detections are related to **video playback functionality** (Exoplayer)
- This is expected behavior for a video player component
- The screen stays on during video playback, which is standard UX
- **Low risk** - not a persistent wake lock for the main app experience

---

## 3. Legal Compliance Check

### Privacy Policy

**Status:** ✅ FOUND (Play Store)  
**URL:** https://whitebit.com/privacy-policy

### Terms & Conditions

**Status:** ❌ NOT FOUND

- Could not locate T&C link on developer website
- Developer website returned 403 Forbidden error (access blocked)
- Subpage probing could not complete

### Data Safety Declaration

**Status:** ✅ COMPLETE

#### Data Collected
| Category | Data Types |
|----------|------------|
| Device or other IDs | Device or other IDs |
| App info and performance | Crash logs, Diagnostics |
| Personal info | Name, Email address, User IDs, Address, Phone number |

#### Data Shared
| Category | Data Types |
|----------|------------|
| Device or other IDs | Device or other IDs |
| Personal info | Name, User IDs, Address, Phone number |

#### Security Practices
- ✅ Data is encrypted in transit
- ✅ You can request that data be deleted

### Developer Contact
- **Website:** https://whitebit.com/
- **Email:** info@whitebit.com

---

## 4. Action Items

### Required Actions

1. **Play Integrity Verification** (REQUIRED)
   - Contact WhiteBit developer team
   - Confirm that KNOWN_ installers (including Digital Turbine) are allowed through their Play Integrity implementation
   - Get written confirmation before proceeding with DT preload

### Optional Actions

2. **Terms & Conditions**
   - Request T&C link from developer
   - Alternatively, verify T&C exists in-app or at alternate URL

---

## Technical Details

- **APK Type:** Split APK bundle (base + config splits)
- **DEX Files:** 8
- **Total Classes:** 70,618
- **Unique Strings:** 396,226

### Files Analyzed
- `base.apk` (131.6 MB)
- `split_config.arm64_v8a.apk`
- `split_config.en.apk`
- `split_config.xhdpi.apk`
- `split_config.xxhdpi.apk`
- `split_config.xxxhdpi.apk`
- `split_config.hdpi.apk`
- `split_config.x86_64.apk`
