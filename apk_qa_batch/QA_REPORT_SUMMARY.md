# APK QA Analysis Report

**Date:** 2026-03-19  
**Total APKs Analyzed:** 28  
**Analysis Types:** Play Integrity & Wake Lock Detection

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Play Integrity - FAIL** | 2 |
| **Play Integrity - WARNING** | 7 |
| **Play Integrity - PASS** | 19 |
| **Wake Lock Detected** | 18 |
| **Wake Lock Not Detected** | 10 |

---

## Critical Issues (FAIL)

### 1. Grammarly Keyboard
- **Package:** `com.grammarly.android.keyboard`
- **File:** `c9f4a477-8b69-4793-9a87-45f994732ec8.apks`
- **Issue:** **Auto Protect (pairip) detected**
- **Impact:** Will block ALL non-Play installs including Digital Turbine preloads
- **Action Required:** Developer must disable Auto Protection in Play Console and upload a new build

### 2. Rocket League Sideswipe
- **Package:** `com.Psyonix.RL2D`
- **File:** `6a442a22-5e76-4e1a-a449-53dd8295bd76.apk`
- **Issue:** **Legacy Play Licensing (LVL) detected**
- **Impact:** Blocks all non-Play installs with no KNOWN_ installer exemption
- **Wake Lock:** YES (high confidence)

---

## Warnings (Requires Manual Verification)

The following 7 apps use **Play Integrity API**, which cannot be determined statically whether DT installs are permitted:

| # | App Name | Package | Wake Lock |
|---|----------|---------|-----------|
| 1 | Solitaire | `com.brainium.solitairefree` | YES (high) |
| 2 | Monumental | `com.mse.monumentalnetworks` | YES (medium) |
| 3 | Garden of Words | `com.iscoolentertainment.snc` | YES (high) |
| 4 | Pure Sniper | `com.miniclip.realsniper` | YES (high) |
| 5 | BIGO LIVE | `sg.bigo.live` | YES (medium) |
| 6 | Ball Sort | `com.kiwifun.game.android.ball.sort` | YES (high) |
| 7 | Brain Blow | `brain.blow.quest` | YES (high) |

**Action Required:** Confirm with developers that KNOWN_ installers (including Digital Turbine) are allowed through.

---

## Passed Apps (No Blocking Protections)

| # | App Name | Package | Wake Lock | Wake Lock Confidence |
|---|----------|---------|-----------|---------------------|
| 1 | Kwai | `com.kwai.video` | NO | high |
| 2 | MyQuest | `com.myquest` | NO | high |
| 3 | Assassin | `com.rubygames.assassin` | YES | high |
| 4 | Mobile Services Manager | `com.LogiaGroup.LogiaDeck` | NO | high |
| 5 | JustWatch | `com.justwatch.justwatch` | NO | high |
| 6 | The Hidden Antique Shop | `io.mobitech.game.hiddenantique` | NO | high |
| 7 | Meditopia | `app.meditasyon` | YES | medium |
| 8 | Idle Bank Tycoon | `com.luckyskeletonstudios.idlebanktycoon` | YES | high |
| 9 | Mint | `com.mint` | NO | high |
| 10 | Sketchbook | `com.adsk.sketchbook` | NO | high |
| 11 | Movistar TV | `ar.onvideo` | NO | high |
| 12 | Plink | `tech.plink.PlinkApp` | YES | medium |
| 13 | GOT: Conquest | `com.wb.goog.got.conquest` | YES | high |
| 14 | Hipi | `com.zee5.hipi` | YES | medium |
| 15 | Tonos de espera | `pe.com.rbt.android` | NO | high |
| 16 | Cyber Music Rush | `com.pianonbeat.rhythm` | YES | high |
| 17 | Gun Blast | `com.gazeus.balls.shooter.game` | YES | low (needs review) |
| 18 | Word Connect | `com.wordgame.words.connect` | YES | medium |
| 19 | Rádio Brasil | `com.appmind.radios.br` | YES | medium |

---

## Wake Lock Detection Summary

Apps with wake lock behavior will keep the screen on during specific activities:

| Confidence | Count | Description |
|------------|-------|-------------|
| **High** | 12 | Confirmed wake lock code in main activity chain |
| **Medium** | 5 | Wake lock in secondary activities or SDK code |
| **Low** | 1 | Needs manual review |

### Apps with Wake Lock (by confidence):

**High Confidence (12 apps):**
- Assassin (`com.rubygames.assassin`)
- Solitaire (`com.brainium.solitairefree`)
- RL Sideswipe (`com.Psyonix.RL2D`)
- Idle Bank Tycoon (`com.luckyskeletonstudios.idlebanktycoon`)
- GOT: Conquest (`com.wb.goog.got.conquest`)
- Garden of Words (`com.iscoolentertainment.snc`)
- Pure Sniper (`com.miniclip.realsniper`)
- Ball Sort (`com.kiwifun.game.android.ball.sort`)
- Brain Blow (`brain.blow.quest`)
- Cyber Music Rush (`com.pianonbeat.rhythm`)

**Medium Confidence (5 apps):**
- Meditopia (`app.meditasyon`)
- Monumental (`com.mse.monumentalnetworks`)
- Plink (`tech.plink.PlinkApp`)
- Hipi (`com.zee5.hipi`)
- BIGO LIVE (`sg.bigo.live`)
- Word Connect (`com.wordgame.words.connect`)
- Rádio Brasil (`com.appmind.radios.br`)

**Low Confidence - Manual Review Required (1 app):**
- Gun Blast (`com.gazeus.balls.shooter.game`) - MediaPlayer wake lock only

---

## Files Generated

| File | Description |
|------|-------------|
| `qa_reports/qa_report_20260319_170141.json` | Full JSON report with detailed analysis |
| `qa_reports/qa_report_20260319_170141.csv` | CSV spreadsheet for easy filtering |
| `QA_REPORT_SUMMARY.md` | This summary document |

---

## Methodology

### Play Integrity Analysis
- **Auto Protect (pairip):** Detects Google's injected protection library
- **Play Integrity API:** Detects usage of integrity verification APIs
- **Legacy Play Licensing (LVL):** Detects older license verification methods

### Wake Lock Analysis
- **Window.addFlags(FLAG_KEEP_SCREEN_ON):** Standard wake lock method
- **View.setKeepScreenOn(true):** Layout-based wake lock
- **PowerManager.newWakeLock:** System-level wake lock
- **MediaPlayer.setScreenOnWhilePlaying:** Media playback wake lock
- **AXML keepScreenOn:** Layout attribute wake lock

---

*Report generated automatically by APK QA Batch Analysis Tool*
