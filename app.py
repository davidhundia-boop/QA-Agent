"""
DT Pre-Sales Play Integrity Screener
Streamlit front-end for play_integrity_analyzer.py.
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import time

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apk_fetcher import extract_package_name, fetch_apk
from play_integrity_analyzer import PlayIntegrityAnalyzer


# ============================================================================
# Page config  (must be first Streamlit call)
# ============================================================================

st.set_page_config(
    page_title="DT Pre-Sales Screener",
    page_icon="🔍",
    layout="centered",
)

st.markdown("""
<style>
    .block-container { max-width: 800px; padding-top: 2rem; }

    /* Result cards */
    .result-pass {
        background: linear-gradient(135deg, #0d3320, #1a4a30);
        border: 1px solid #2d6b45;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
    }
    .result-warning {
        background: linear-gradient(135deg, #3d2e0a, #4a3a12);
        border: 1px solid #8a7a30;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
    }
    .result-fail {
        background: linear-gradient(135deg, #3d0a0a, #4a1212);
        border: 1px solid #8a3030;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
    }
    .result-error {
        background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
        border: 1px solid #444444;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
    }
    .app-header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 14px;
    }
    .app-header img {
        width: 48px;
        height: 48px;
        border-radius: 10px;
        flex-shrink: 0;
    }
    .app-name  { font-size: 1.15em; font-weight: 600; line-height: 1.3; }
    .pkg-name  { font-size: 0.82em; opacity: 0.55; margin-top: 2px; }
    .status-badge { font-size: 1.05em; font-weight: 500; }

    /* Blue primary button */
    .stButton > button[kind="primary"] {
        background-color: #0066cc !important;
        color: white !important;
        border: none !important;
        padding: 0.45rem 2rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0052a3 !important;
    }

    /* Tidy the tab bar */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"]      { border-radius: 6px 6px 0 0; }

    /* Hide Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Helpers
# ============================================================================

def get_app_metadata(package_name: str) -> dict:
    """Return {title, icon} — cached in session_state to avoid repeat fetches."""
    cache = st.session_state.setdefault("metadata_cache", {})
    if package_name in cache:
        return cache[package_name]
    result = {"title": package_name, "icon": None}
    try:
        from google_play_scraper import app as gps_app
        data = gps_app(package_name, lang="en", country="us")
        result = {
            "title": data.get("title") or package_name,
            "icon": data.get("icon"),
        }
    except Exception:
        pass
    cache[package_name] = result
    return result


def run_analyzer(apk_path: str) -> tuple[dict, str]:
    """Run PlayIntegrityAnalyzer silently. Returns (to_json() dict, log text)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        analyzer = PlayIntegrityAnalyzer(apk_path)
        analyzer.analyze()
    return analyzer.to_json(), buf.getvalue()


def analyze_apk_bytes(apk_bytes: bytes, label: str) -> dict:
    """Write *apk_bytes* to a temp file, run the analyzer, return result dict."""
    tmp = tempfile.NamedTemporaryFile(suffix=".apk", delete=False)
    try:
        tmp.write(apk_bytes)
        tmp.close()
        analysis, _ = run_analyzer(tmp.name)
        analysis["app_name"] = label
        return analysis
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def verdict_display(result: dict) -> dict:
    """Map an analyzer result to display metadata (css_class, color, messages)."""
    verdict = result.get("verdict", "ERROR")
    fail_ids = [
        item.get("id", "")
        for item in result.get("details", {}).get("fail", [])
    ]

    if verdict == "FAIL":
        messages = []
        if "pairip_auto_protect" in fail_ids:
            messages.append(
                "❌ FAIL — Auto Protect enabled. "
                "Client must disable in Play Console + upload new build."
            )
        if "legacy_play_licensing" in fail_ids:
            messages.append(
                "❌ FAIL — Legacy Play Licensing blocks sideloaded installs."
            )
        if not messages:
            messages.append("❌ FAIL — Blocking protection detected.")
        return {"css": "result-fail", "color": "#ff6b6b", "messages": messages}

    if verdict == "WARNING":
        return {
            "css": "result-warning",
            "color": "#ffc94d",
            "messages": [
                "⚠️ WARNING — Uses Play Integrity API. "
                "Server-side enforcement unknown. Verify with client."
            ],
        }

    if verdict == "PASS":
        return {
            "css": "result-pass",
            "color": "#4ade80",
            "messages": ["✅ PASS — No Play Integrity blockers detected."],
        }

    if verdict == "INCONCLUSIVE":
        return {
            "css": "result-error",
            "color": "#aaaaaa",
            "messages": [
                "⚙️ INCONCLUSIVE — Could not fully analyze APK. Manual testing required."
            ],
        }

    return {
        "css": "result-error",
        "color": "#aaaaaa",
        "messages": ["⚙️ ERROR — Could not download APK."],
    }


def render_result(result: dict):
    """Render one color-coded HTML card + a collapsible details section."""
    disp = verdict_display(result)
    app_name = result.get("app_name") or result.get("package", "Unknown")
    package  = result.get("package", "")
    icon_url = result.get("icon", "")

    icon_html = f'<img src="{icon_url}" />' if icon_url else "📦"
    pkg_html  = f'<div class="pkg-name">{package}</div>' if package and package != app_name else ""
    badges    = "".join(
        f'<div class="status-badge" style="color:{disp["color"]}">{m}</div>'
        for m in disp["messages"]
    )

    st.markdown(
        f"""
        <div class="{disp['css']}">
          <div class="app-header">
            {icon_html}
            <div>
              <div class="app-name">{app_name}</div>
              {pkg_html}
            </div>
          </div>
          {badges}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Details expander — internal use only
    fail_items = result.get("details", {}).get("fail", [])
    warn_items = result.get("details", {}).get("warning", [])
    error_msg  = result.get("error")

    with st.expander("Technical details  *(internal — do not share with client)*"):
        if error_msg:
            st.code(error_msg)
        elif not fail_items and not warn_items:
            st.write("No issues detected.")
            st.caption(f"DEX strings analyzed: {result.get('dex_string_count', 'N/A')}")
        else:
            for item in fail_items:
                st.markdown(f"**[FAIL] {item['name']}**")
                st.write(item.get("description", ""))
                if item.get("evidence"):
                    st.code("\n".join(item["evidence"][:10]))
            for item in warn_items:
                st.markdown(f"**[WARNING] {item['name']}**")
                st.write(item.get("description", ""))
                if item.get("evidence"):
                    st.code("\n".join(item["evidence"][:10]))


# ============================================================================
# Header
# ============================================================================

st.title("🔍 DT Pre-Sales Screener")
st.caption("Check if an app will block DT preloads before you pitch")

# ============================================================================
# Session state
# ============================================================================

st.session_state.setdefault("single_result", None)
st.session_state.setdefault("bulk_results", [])

# ============================================================================
# Tabs
# ============================================================================

tab_single, tab_bulk = st.tabs(["Single App", "Bulk"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Single App
# ─────────────────────────────────────────────────────────────────────────────

with tab_single:
    st.subheader("Analyze a single app")

    input_val = st.text_input(
        "Paste a Google Play URL or package name",
        placeholder="https://play.google.com/store/apps/details?id=com.example.app",
        key="single_input",
    )

    st.divider()
    uploaded_apk = st.file_uploader(
        "Or upload an APK directly",
        type=["apk"],
        key="single_apk_upload",
        help="Use this if auto-download fails",
    )

    analyze_clicked = st.button("Analyze", type="primary", key="single_btn")

    if analyze_clicked:
        # ── Path A: uploaded APK ──────────────────────────────────────────
        if uploaded_apk is not None:
            with st.spinner("Analyzing uploaded APK…"):
                result = analyze_apk_bytes(uploaded_apk.read(), uploaded_apk.name)
                result.setdefault("details", {})
            st.session_state.single_result = result

        # ── Path B: URL / package name ────────────────────────────────────
        elif input_val.strip():
            try:
                package_name = extract_package_name(input_val.strip())
            except ValueError as exc:
                st.error(str(exc))
                st.stop()

            result: dict = {"package": package_name}

            with st.spinner("Fetching app metadata…"):
                meta = get_app_metadata(package_name)
                result["app_name"] = meta["title"]
                result["icon"]     = meta.get("icon")

            tmp_dir = tempfile.mkdtemp(prefix="pi_screener_")
            try:
                with st.spinner(f"Downloading APK for **{meta['title']}**…"):
                    apk_path = fetch_apk(package_name, tmp_dir)

                with st.spinner("Analyzing…"):
                    analysis, _ = run_analyzer(apk_path)
                    result.update(analysis)
                    result["app_name"] = meta["title"]
                    result["icon"]     = meta.get("icon")

            except Exception as exc:
                result["verdict"] = "ERROR"
                result["error"]   = str(exc)
                result.setdefault("details", {})

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

            st.session_state.single_result = result

        else:
            st.warning("Enter a URL / package name, or upload an APK file.")

    # Render persisted result (survives Streamlit reruns / expander clicks)
    if st.session_state.single_result:
        st.markdown("---")
        render_result(st.session_state.single_result)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Bulk
# ─────────────────────────────────────────────────────────────────────────────

with tab_bulk:
    st.subheader("Analyze multiple apps")

    col_text, col_csv = st.columns([2, 1])

    with col_text:
        bulk_text = st.text_area(
            "One URL or package name per line",
            height=160,
            placeholder=(
                "com.example.app1\n"
                "https://play.google.com/store/apps/details?id=com.example.app2\n"
                "com.example.app3"
            ),
            key="bulk_text",
        )

    with col_csv:
        st.write("")
        st.write("")
        uploaded_csv = st.file_uploader(
            "Or upload CSV",
            type=["csv"],
            help="CSV must have a **url** or **package_name** column",
            key="bulk_csv",
        )

    if st.button("Analyze All", type="primary", key="bulk_btn"):
        inputs: list[str] = []

        if uploaded_csv:
            try:
                df_up = pd.read_csv(uploaded_csv)
                col = next(
                    (c for c in ("url", "package_name") if c in df_up.columns), None
                )
                if col:
                    inputs.extend(str(v) for v in df_up[col].dropna())
                else:
                    st.warning("CSV must have a 'url' or 'package_name' column. File ignored.")
            except Exception as exc:
                st.warning(f"Could not read CSV: {exc}")

        for line in bulk_text.strip().splitlines():
            line = line.strip()
            if line:
                inputs.append(line)

        if not inputs:
            st.warning("No inputs provided.")
        else:
            # Pre-parse to catch bad inputs immediately
            parsed: list[tuple[str, str | None, str | None]] = []
            for raw in inputs:
                try:
                    parsed.append((raw, extract_package_name(raw.strip()), None))
                except ValueError as exc:
                    parsed.append((raw, None, str(exc)))

            total = len(parsed)
            st.info(f"Processing {total} app(s)…")
            progress = st.progress(0)
            status   = st.empty()

            # Pre-allocate one result slot per app so results appear in order
            slots = [st.empty() for _ in range(total)]
            results: list[dict] = []

            for idx, (original, pkg, parse_err) in enumerate(parsed):
                label = pkg or original
                status.text(f"[{idx + 1}/{total}] {label}…")

                if parse_err:
                    r = {
                        "input": original, "package": original, "app_name": original,
                        "verdict": "ERROR", "error": parse_err,
                        "icon": None, "details": {},
                    }
                else:
                    tmp_dir = tempfile.mkdtemp(prefix="pi_screener_")
                    try:
                        meta     = get_app_metadata(pkg)
                        apk_path = fetch_apk(pkg, tmp_dir)
                        analysis, _ = run_analyzer(apk_path)
                        r = dict(analysis)
                        r.update({"input": original, "app_name": meta["title"],
                                  "icon": meta.get("icon"), "package": pkg})
                    except Exception as exc:
                        meta = get_app_metadata(pkg) if pkg else {"title": original}
                        r = {
                            "input": original, "package": pkg or original,
                            "app_name": meta["title"], "verdict": "ERROR",
                            "error": str(exc), "icon": None, "details": {},
                        }
                    finally:
                        shutil.rmtree(tmp_dir, ignore_errors=True)

                results.append(r)

                # Render this result immediately into its pre-allocated slot
                with slots[idx]:
                    render_result(r)

                progress.progress((idx + 1) / total)
                if idx < total - 1:
                    time.sleep(2)

            status.text("Analysis complete.")
            st.session_state.bulk_results = results

    # ── Render persisted results (after page reruns) ──────────────────────
    elif st.session_state.bulk_results:
        results = st.session_state.bulk_results
        SORT_KEY = {"FAIL": 0, "WARNING": 1, "INCONCLUSIVE": 2, "PASS": 3, "ERROR": 4}
        sorted_results = sorted(
            results, key=lambda r: SORT_KEY.get(r.get("verdict", "ERROR"), 99)
        )

        st.markdown("---")
        st.subheader("Results")
        for r in sorted_results:
            render_result(r)
            st.divider()

        # ── CSV export ────────────────────────────────────────────────────
        VERDICT_LABEL = {
            "FAIL": "❌ FAIL", "WARNING": "⚠️ WARNING", "PASS": "✅ PASS",
            "INCONCLUSIVE": "⚙️ INCONCLUSIVE", "ERROR": "⚙️ ERROR",
        }
        export_rows = []
        for r in sorted_results:
            disp = verdict_display(r)
            verdict = r.get("verdict", "ERROR")
            export_rows.append({
                "App Name":       r.get("app_name", ""),
                "Package":        r.get("package", ""),
                "Verdict":        VERDICT_LABEL.get(verdict, verdict),
                "Message":        "; ".join(disp["messages"]),
                "Fail Reasons":   ", ".join(i["name"] for i in r.get("details", {}).get("fail", [])),
                "Warning Reasons": ", ".join(i["name"] for i in r.get("details", {}).get("warning", [])),
                "Error":          r.get("error", ""),
            })

        st.download_button(
            label="⬇️ Export CSV",
            data=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8"),
            file_name="play_integrity_results.csv",
            mime="text/csv",
        )
