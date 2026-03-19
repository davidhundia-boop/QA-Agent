# App QA Report: SoFi (com.sofi.mobile)

**Date:** 2026-03-16  
**Version:** 3.68.2 (170852905)  
**Package:** com.sofi.mobile  
**Developer:** Social Finance, LLC  
**Source URL:** https://whitelabel-cdn-prod.digitalturbine.com/files/042c6dba-93e8-4958-a27d-a34d273a0007.apks

---

## Overall Verdict: FAIL

This APK **cannot be preinstalled** via Digital Turbine in its current form.

---

## 1. Play Integrity Analysis

### Verdict: FAIL

| Check | Status | Details |
|-------|--------|---------|
| Auto Protect (pairip) | **FAIL** | 40 indicators detected |
| Play Integrity API | WARNING | 6 indicators - needs manual verification |
| Legacy Play Licensing | PASS | No blocking evidence |

### Critical Issue: Auto Protect (pairip) Detected

Google injects the pairip library at Play Console upload time. **This blocks ALL non-Play installs including Digital Turbine.**

**Required Action:** The developer must disable Auto Protection in Play Console and upload a new build.

**Evidence (sample):**
- `Lcom/pairip/licensecheck/LicenseClient;`
- `Lcom/pairip/licensecheck/LicenseActivity;`
- `Lcom/pairip/SignatureCheck$SignatureTamperedException;`
- `Lcom/pairip/VMRunner;`

### Warning: Play Integrity API

App uses Play Integrity API. Cannot determine statically whether DT installs are permitted (verdict handling is server-side).

**Required Action:** Confirm with the developer that KNOWN installers (including Digital Turbine) are allowed through their server-side policy.

---

## 2. Wake Lock Analysis

### Verdict: MEDIUM CONFIDENCE (Acceptable)

| Field | Value |
|-------|-------|
| Wake Lock Detected | Yes |
| Confidence | Medium |
| Manual Review Needed | No |

**Findings:**
- `keepScreenOn=true` found in `res/layout/misnap_your_camera_overlay.xml`
- `keepScreenOn=true` found in `res/layout/misnap_your_camera_overlay_ux2.xml`

**Assessment:** These wake locks are in MiSnap SDK camera overlay layouts used for document capture (identity verification). This is expected and acceptable behavior for a banking app - not a concern for DT preload.

---

## 3. Legal Compliance Check

### Verdict: WARNING

| Check | Status | Detail |
|-------|--------|--------|
| Privacy Policy | PASS | Found on Play Store |
| Terms & Conditions | FAIL | Not found |
| Data Safety | Skipped | Playwright not installed |

**Privacy Policy URL:** https://www.sofi.com/online-privacy-policy

**Developer Contact:**
- Website: www.sofi.com
- Email: mobilesupport@sofi.com

**Notes:**
- Developer website returned 403 Forbidden when crawled
- Terms & Conditions link not found in Play Store listing

---

## App Details

| Property | Value |
|----------|-------|
| Package Name | com.sofi.mobile |
| App Name | SoFi: Bank, Investing & Crypto |
| Version Name | 3.68.2 |
| Version Code | 170852905 |
| Min SDK | 26 (Android 8.0) |
| Target SDK | 35 (Android 15) |
| Framework | Flutter |
| Main Activity | com.sofi.mobile.MainActivity |

### Key Permissions
- `ACCESS_FINE_LOCATION`
- `INTERNET`
- (and others)

---

## Summary & Next Steps

### Blockers
1. **Auto Protect (pairip)** - Must be disabled by developer before DT preload is possible

### Action Items
1. Contact SoFi developer team to request:
   - Disable Auto Protection in Play Console
   - Rebuild and provide new APK
   - Confirm Play Integrity API policy allows Digital Turbine installer
2. Request Terms & Conditions URL for legal compliance

### Recommendation
**DO NOT PROCEED** with preload until Auto Protection is disabled.
