# QA Report: WhiteBIT (com.whitebit.android)

**Version:** 3.70.0  
**Target SDK:** 36  
**Min SDK:** 24  
**Analysis Date:** 2026-03-18  
**Source:** https://whitelabel-cdn-prod.digitalturbine.com/files/26b417db-95ee-4530-91ed-baac8a75cab7.apks

---

## Summary

| Check | Result | Status |
|-------|--------|--------|
| Legal Compliance | WARNING | Privacy Policy found, T&C not found |
| Play Integrity | WARNING | API detected, needs developer confirmation |
| Wake Lock | FLAGGED | Medium confidence detection |

---

## 1. Legal Compliance Check

**Rating:** ⚠️ WARNING

| Check | Status | Detail |
|-------|--------|--------|
| Privacy Policy | ✅ FOUND | Play Store |
| Terms & Conditions | ❌ NOT FOUND | - |
| Data Safety | — | Skipped (Playwright not installed) |

### Details
- **Privacy Policy URL:** https://whitebit.com/privacy-policy
- **Developer Website:** whitebit.com
- **Developer Email:** info@whitebit.com

### Notes
- Developer website (https://whitebit.com/) returned 403 Forbidden, preventing T&C link crawling
- Privacy Policy is available on Play Store listing

---

## 2. Play Integrity & App Protection Analysis

**Verdict:** ⚠️ WARNING

| Check | Result |
|-------|--------|
| Auto Protect (pairip) | ✅ Not detected |
| Play Integrity API | ⚠️ Detected (6 indicators) |
| Legacy Play Licensing (LVL) | ✅ Not detected |

### Play Integrity API Evidence
The app uses Google's Play Integrity API with the following indicators detected:
1. `com.google.android.play.core.integrity.protocol.IIntegrityService`
2. `IntegrityTokenRequest`
3. `IntegrityTokenResponse`
4. `StandardIntegrityManager`

### Action Required
**Manual verification needed:** Cannot determine statically whether Digital Turbine installs are permitted. The verdict handling is server-side. Developer must confirm that KNOWN_ installers (including Digital Turbine) are allowed through their integrity validation.

---

## 3. Wake Lock / Screen Hold Analysis

**Result:** ⚠️ FLAGGED  
**Confidence:** Medium

### Detections

| Vector | Location | Tier | Notes |
|--------|----------|------|-------|
| Window.addFlags(FLAG_KEEP_SCREEN_ON) | `com.brentvatne.exoplayer.FullScreenPlayerView$KeepScreenOnUpdater.run()` | 3 | Video player component |
| AXML keepScreenOn=true | `res/layout/sns_fragment_video_ident.xml` | 3 | Video identification layout |

### Analysis
Both detections are related to **video playback functionality**:
- **ExoPlayer FullScreenPlayerView** - Keeps screen on during full-screen video playback only
- **Video Identification Layout** - Likely used for KYC video verification feature

These are **scoped wake locks** that only apply during video playback, not the main app experience. This is expected behavior for a cryptocurrency exchange app that may have video-based identity verification.

---

## Overall Assessment

### ⚠️ CONDITIONAL APPROVAL RECOMMENDED

**Blocking Issues:** None

**Items Requiring Action:**
1. **Play Integrity API** - Developer must confirm Digital Turbine is whitelisted as an approved installer
2. **Terms & Conditions** - Could not be verified due to website 403 error (may need to check manually)

**Acceptable Findings:**
- Wake lock detections are scoped to video playback features (ExoPlayer, video identification)
- Privacy Policy is properly configured on Play Store
- No pairip/Auto Protect blocking
- No Legacy Play Licensing blocking

### Recommendation
Proceed with preload pending developer confirmation that Play Integrity API is configured to accept Digital Turbine as a KNOWN_ installer.

---

## Technical Details

- **DEX Files Analyzed:** 8
- **Total Unique Strings:** 396,226
- **Classes Scanned (Wake Lock):** 1,678 / 70,618
- **Analysis Time:** ~4 seconds total
