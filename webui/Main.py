"""VideoPrinterTurbo WebUI — Streamlit frontend with i18n support.

Language detection priority:
  1. URL query param ?lang=xx (set by JS reading localStorage or browser)
  2. config.toml [ui] language
  3. System locale
"""

import json
import locale
import os
import sys

import requests
import streamlit as st
from loguru import logger

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.config import config


# ── i18n setup ─────────────────────────────────────────────────────

_i18n_dir = os.path.join(root_dir, "webui", "i18n")


def _load_locales(i18n_dir: str) -> dict:
    locales = {}
    if not os.path.isdir(i18n_dir):
        return locales
    for file in os.listdir(i18n_dir):
        if file.endswith(".json"):
            lang = file[:-5]
            with open(os.path.join(i18n_dir, file), "r", encoding="utf-8") as f:
                locales[lang] = json.load(f)
    return locales


locales = _load_locales(_i18n_dir)


def _get_system_locale() -> str:
    try:
        loc = locale.getlocale()
        return loc[0].split("_")[0] if loc[0] else "en"
    except Exception:
        return "en"


def _resolve_language() -> str:
    """Determine language: URL param > config > system locale."""
    lang = st.query_params.get("lang")
    if lang and lang in locales:
        return lang
    if config.ui.language:
        return config.ui.language
    return _get_system_locale()


def tr(key: str) -> str:
    lang = st.session_state.get("ui_language", "zh")
    loc = locales.get(lang, {})
    return loc.get("Translation", {}).get(key, key)


# ── Page config (must be first Streamlit command) ───────────────────

st.set_page_config(
    page_title="VideoPrinterTurbo",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── Language init ──────────────────────────────────────────────────

if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = _resolve_language()
    if st.session_state["ui_language"] not in locales and locales:
        st.session_state["ui_language"] = list(locales.keys())[0]


# ── JS: localStorage language detection (one-shot) ─────────────────
# On first visit without ?lang=, inject JS to read localStorage or
# detect browser language, save to localStorage, then redirect to
# ?lang=xxx. On subsequent visits ?lang= is present so this skips.

if "lang" not in st.query_params and "_lang_js_injected" not in st.session_state:
    st.session_state["_lang_js_injected"] = True
    from streamlit.components.v1 import html

    html(
        """
        <script>
        (function() {
            // Guard: if URL already has ?lang=, Streamlit just hasn't surfaced it yet — skip.
            if (new URL(window.top.location).searchParams.get('lang')) return;
            var saved = localStorage.getItem('vpt_lang');
            var lang;
            if (saved) {
                lang = saved;
            } else {
                lang = (navigator.language || '').split('-')[0] || 'en';
                localStorage.setItem('vpt_lang', lang);
            }
            var url = new URL(window.top.location);
            url.searchParams.set('lang', lang);
            window.top.location.replace(url.toString());
        })();
        </script>
        """,
        height=1,
        width=1,
    )

# ── Language change callback (runs before script body on widget change) ─

def _on_language_change():
    selected = st.session_state.get("top_language_selector", "")
    if selected:
        code = selected.split(" - ")[0].strip()
        if code in locales:
            st.session_state["ui_language"] = code
            st.query_params["lang"] = code


# ── Top bar: title + language selector ─────────────────────────────

title_col, lang_col = st.columns([3, 1])

with title_col:
    st.title(f"🎬 {tr('VideoPrinterTurbo')} — {tr('Video Rewriting AI')}")

with lang_col:
    if locales:
        lang_options = []
        selected_idx = 0
        for i, code in enumerate(locales.keys()):
            label = f"{code} - {locales[code].get('Language', code)}"
            lang_options.append(label)
            if code == st.session_state.get("ui_language", ""):
                selected_idx = i

        st.selectbox(
            tr("Language / 语言"),
            options=lang_options,
            index=selected_idx,
            key="top_language_selector",
            label_visibility="collapsed",
            on_change=_on_language_change,
        )
        # Keep localStorage in sync so first-visit detection stays accurate
        from streamlit.components.v1 import html as _html
        _html(
            f"<script>try{{localStorage.setItem('vpt_lang','{st.session_state.get('ui_language','zh')}')}}catch(e){{}}</script>",
            height=1,
            width=1,
        )

# ── API base URL ───────────────────────────────────────────────────

_api_base = os.getenv("VPT_API_BASE", "http://127.0.0.1:8080")


def _api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{_api_base}{path}", timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("data") if data.get("status") == 200 else None
    except Exception as e:
        st.error(f"{tr('Cannot connect to API service.')} ({e})")
        return None


def _api_post(path: str, body: dict) -> dict | None:
    try:
        r = requests.post(f"{_api_base}{path}", json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("data") if data.get("status") == 200 else None
    except Exception as e:
        st.error(f"{tr('Task submission failed, please check the API server.')} ({e})")
        return None


def _api_delete(path: str) -> bool:
    try:
        r = requests.delete(f"{_api_base}{path}", timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        st.error(f"{tr('Cannot connect to API service.')} ({e})")
        return False


def _api_stop(task_id: str) -> bool:
    try:
        r = requests.post(f"{_api_base}/api/v1/tasks/{task_id}/stop", timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        st.error(f"{tr('Cannot connect to API service.')} ({e})")
        return False


# ── Sidebar ────────────────────────────────────────────────────────

with st.sidebar:
    st.header(tr("Settings"))

    llm_options = {
        "openai": tr("OpenAI / DeepSeek / Compatible"),
        "gemini": tr("Google Gemini"),
    }
    current_llm = config.app.llm_provider
    default_llm = current_llm if current_llm in llm_options else "openai"
    selected_llm = st.selectbox(
        tr("LLM Provider"),
        options=list(llm_options.keys()),
        format_func=lambda x: llm_options.get(x, x),
        index=list(llm_options.keys()).index(default_llm) if default_llm in llm_options else 0,
    )

    voice_name = st.text_input(
        tr("Voice"),
        value=config.app.get("voice_name", "zh-CN-XiaoxiaoNeural-Female"),
    )
    voice_rate = st.slider(tr("Speed"), min_value=0.5, max_value=2.0, value=1.0, step=0.1)

    bgm_type = st.selectbox(tr("Background Music"), options=["random", "none"],
                            format_func=lambda x: tr(x), index=0)
    bgm_volume = st.slider(tr("BGM Volume"), min_value=0.0, max_value=1.0, value=0.2, step=0.1)

    subtitle_enabled = st.checkbox(tr("Subtitles"), value=True)
    subtitle_position = st.selectbox(tr("Subtitle Position"), options=["bottom", "top", "center"],
                                     format_func=lambda x: tr(x), index=0)

    aspect_labels = {
        "9:16": tr("Portrait 9:16"),
        "16:9": tr("Landscape 16:9"),
        "1:1": tr("Square 1:1"),
    }
    selected_aspect = st.selectbox(
        tr("Aspect Ratio"),
        options=list(aspect_labels.keys()),
        format_func=lambda x: aspect_labels.get(x, x),
        index=0,
    )

    video_source = st.selectbox(tr("Video Source"), options=["pexels", "pixabay", "local"], index=0)

    auto_publish = st.checkbox(tr("Auto Publish"), value=False)
    publish_platforms = ""
    if auto_publish:
        publish_platforms = st.text_input(tr("Publish Platforms (comma separated)"),
                                          value="tiktok, instagram")

    with st.expander(tr("Advanced Options")):
        video_count = st.number_input(tr("Video Count"), min_value=1, max_value=5, value=1)
        clip_duration = st.number_input(tr("Clip Duration (s)"), min_value=2, max_value=15, value=5)
        font_size = st.number_input(tr("Font Size"), min_value=30, max_value=120, value=60)
        n_threads = st.number_input(tr("Threads"), min_value=1, max_value=8, value=2)

# ── Main panel ─────────────────────────────────────────────────────

st.subheader(tr("Input"))

# Pre-fill from edit action
_edit_params = st.session_state.get("edit_task_params", {})
if _edit_params:
    edit_notice_col, cancel_col = st.columns([4, 1])
    with edit_notice_col:
        st.info(tr("Editing task") + f": {_edit_params.get('task_id', '')[:8]}…")
    with cancel_col:
        if st.button(tr("Cancel Edit"), use_container_width=True):
            st.session_state.pop("edit_task_params", None)
            st.rerun()

video_url = st.text_input(
    tr("Video URL"),
    value=_edit_params.get("video_url", ""),
    placeholder=tr("Video URL placeholder"),
)

rewrite_instruction = st.text_area(
    tr("Rewrite Instruction"),
    value=_edit_params.get("rewrite_instruction", ""),
    placeholder=tr("Rewrite Instruction placeholder"),
    height=100,
)

video_script = st.text_area(
    tr("Custom Script (optional, leave empty for AI)"),
    value=_edit_params.get("video_script", ""),
    placeholder=tr("Custom Script placeholder"),
    height=100,
)

submitted = st.button(tr("Start Rewrite"), type="primary", use_container_width=True)

# ── Handle submission ──────────────────────────────────────────────

if submitted:
    if not video_url:
        st.error(tr("Please enter a video URL."))
    else:
        body = {
            "video_url": video_url,
            "rewrite_instruction": rewrite_instruction,
            "video_script": video_script,
            "voice_name": voice_name,
            "voice_rate": voice_rate,
            "bgm_type": bgm_type,
            "bgm_volume": bgm_volume,
            "subtitle_enabled": subtitle_enabled,
            "subtitle_position": subtitle_position,
            "video_aspect": selected_aspect,
            "video_source": video_source,
            "auto_publish": auto_publish,
            "publish_platforms": [p.strip() for p in publish_platforms.split(",") if p.strip()] if publish_platforms else None,
            "video_count": video_count,
            "video_clip_duration": clip_duration,
            "font_size": font_size,
            "n_threads": n_threads,
        }

        result = _api_post("/api/v1/rewrite", body)
        if result:
            task_id = result.get("task_id", "")
            st.success(f"{tr('Task submitted')}: {task_id}")
            st.info(tr("Task is being processed, click Refresh to check progress."))
            st.session_state.pop("edit_task_params", None)
        else:
            st.error(tr("Task submission failed, please check the API server."))

# ── Refresh task list ──────────────────────────────────────────────

if st.button(tr("Refresh Task List")):
    data = _api_get("/api/v1/tasks?page=1&page_size=50")
    if data:
        tasks = data.get("tasks", [])
        total = data.get("total", 0)
        if tasks:
            st.caption(f"{tr('Total')} {total} {tr('tasks')}")
            for t in tasks:
                state_val = t.get("state", 0)
                progress = t.get("progress", 0)
                tid = t.get("task_id", "")
                logs = t.get("logs") or []
                videos = t.get("videos", []) or []

                if state_val == -1:
                    icon, status = "❌", tr("Failed")
                elif state_val == 1:
                    icon, status = "✅", tr("Completed")
                elif state_val == 4:
                    icon, status = "⏳", tr("Processing")
                else:
                    icon, status = "❓", f"{tr('Unknown')}({state_val})"

                tid_short = tid[:8] + "…" if len(tid) > 8 else tid
                with st.expander(f"{icon} {tid_short}  |  {status}  {progress}%"):
                    st.progress(progress / 100)
                    if logs:
                        st.code("\n".join(logs), language=None)
                    else:
                        st.caption(tr("No logs"))
                    if videos:
                        st.write(f"**{tr('Videos')}**")
                        for v in videos:
                            st.markdown(f"[{v.split('/')[-1]}]({v})")

                    # Action buttons
                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        stop_disabled = state_val != 4
                        if st.button(tr("Stop"), key=f"stop_{tid}", disabled=stop_disabled,
                                     use_container_width=True):
                            if _api_stop(tid):
                                st.success(tr("Task stop requested"))
                                st.rerun()
                    with btn_cols[1]:
                        if st.button(tr("Delete"), key=f"del_{tid}", type="primary",
                                     use_container_width=True):
                            if _api_delete(f"/api/v1/tasks/{tid}"):
                                st.success(tr("Task deleted"))
                                st.rerun()
                    with btn_cols[2]:
                        task_params = t.get("params") or {}
                        if st.button(tr("Edit"), key=f"edit_{tid}", use_container_width=True):
                            st.session_state["edit_task_params"] = {
                                **task_params, "task_id": tid
                            }
                            st.rerun()
        else:
            st.info(tr("No Tasks"))
    else:
        st.warning(tr("Cannot connect to API service."))

# ── Footer ─────────────────────────────────────────────────────────

st.markdown("---")
st.caption(tr("Tip: Tasks run in background. Videos are saved in storage/tasks/."))
