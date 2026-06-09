"""Task orchestrator — the main pipeline that drives the video rewrite process.

Pipeline steps:
    ① Download source video          (plugin: downloader)
    ② Extract/transcribe original text (plugin: transcriber)
    ③ LLM rewrite the script         (plugin: llm)
    ④ TTS generate audio             (service: voice)
    ⑤ Search for video materials     (plugin: material)
    ⑥ Compose the final video        (service: video_rewrite)
    ⑦ (Optional) Publish             (plugin: publisher)
"""

import math
import os
import re
from datetime import datetime
from os import path

from loguru import logger

from app.config import config
from app.models import const
from app.models.schema import VideoRewriteParams
from app.plugins.base import PluginRegistry, PluginType
from app.services import voice
from app.services import state as sm
from app.utils import utils


def _log(msg: str) -> str:
    return f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"


def _is_stopped(task_id: str) -> bool:
    t = sm.state.get_task(task_id)
    return t is not None and t.get("stopped") is True


def start(task_id: str, params: VideoRewriteParams, stop_at: str = "video"):
    """Main pipeline entry point — called from the task queue."""
    logger.info(f"start task: {task_id}, stop_at: {stop_at}")
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=0,
                         log=_log("任务已提交，等待执行..."))

    # ── ① Download source video ─────────────────────────────────────
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=5,
                         log=_log("① 开始下载视频..."))
    downloader = _get_plugin(PluginType.DOWNLOADER, "downloader_provider")
    if not downloader:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ 未找到下载插件"))
        return

    logger.info(f"\n## ① downloading video: {params.video_url}")
    try:
        video_pkg = downloader.download(params.video_url)
    except Exception as e:
        logger.error(f"download failed: {e}")
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log(f"❌ 下载失败: {e}"))
        return

    if not video_pkg.video_path or not os.path.isfile(video_pkg.video_path):
        logger.error("download produced no video file")
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ 下载完成但未产生视频文件"))
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=15,
                         source_video=video_pkg.video_path,
                         source_audio=video_pkg.audio_path,
                         source_subtitle=video_pkg.subtitle_path,
                         video_meta=video_pkg.metadata,
                         log=_log("① 视频下载完成"))

    # ── ② Extract / transcribe original text ─────────────────────────
    if _is_stopped(task_id):
        return
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=20,
                         log=_log("② 开始提取 / 转录原文..."))

    transcriber = _get_plugin(PluginType.TRANSCRIBER, "transcriber_provider")
    transcript_segments = []

    # Try subtitle first
    if video_pkg.subtitle_path and os.path.isfile(video_pkg.subtitle_path):
        logger.info(f"\n## ② extracting subtitles from: {video_pkg.subtitle_path}")
        if transcriber:
            transcript_segments = transcriber.extract_subtitles(video_pkg.video_path)

    # Fallback to audio transcription
    if not transcript_segments and video_pkg.audio_path and os.path.isfile(video_pkg.audio_path):
        logger.info(f"\n## ② transcribing audio: {video_pkg.audio_path}")
        if transcriber:
            transcript_segments = transcriber.transcribe(video_pkg.audio_path)

    # Last resort: transcribe from video directly
    if not transcript_segments and os.path.isfile(video_pkg.video_path):
        logger.info(f"\n## ② transcribing video audio directly: {video_pkg.video_path}")
        if transcriber:
            transcript_segments = transcriber.extract_subtitles(video_pkg.video_path)

    if not transcript_segments:
        logger.warning("no transcript could be extracted — continuing with empty source text")

    original_text = "\n".join(seg.text for seg in transcript_segments)
    logger.info(f"extracted {len(transcript_segments)} segments, {len(original_text)} chars")

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=30,
                         transcript_segments=[s.model_dump() for s in transcript_segments],
                         log=_log(f"② 转录完成，{len(transcript_segments)} 个片段，{len(original_text)} 字"))

    if stop_at == "transcript":
        sm.state.update_task(task_id, state=const.TASK_STATE_COMPLETE, progress=100,
                             transcript=original_text)
        return {"transcript": original_text, "segments": transcript_segments}

    # ── ③ LLM rewrite ──────────────────────────────────────────────
    if _is_stopped(task_id):
        return
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=35,
                         log=_log("③ 调用 LLM 改写文案..."))

    llm_provider = _get_plugin(PluginType.LLM, "llm_provider")
    if not llm_provider:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ 未找到 LLM 插件"))
        return

    # Determine rewrite script
    video_script = params.video_script.strip()
    if not video_script:
        logger.info(f"\n## ③ rewriting script via LLM")
        rewrite_instruction = params.rewrite_instruction or "改写这段文案，使其更加生动有趣，适合短视频解说。"
        video_script = llm_provider.rewrite(
            original_text=original_text,
            instruction=rewrite_instruction,
        )
    else:
        logger.info(f"\n## ③ using user-provided script")

    if not video_script:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ LLM 文案生成失败"))
        logger.error("failed to generate video script")
        return

    # Generate search terms
    search_terms = params.video_script or ""
    if not search_terms:
        try:
            search_terms = llm_provider.generate_terms(
                video_subject=params.rewrite_instruction or params.video_url,
                video_script=video_script,
                amount=5,
            )
        except Exception as e:
            logger.warning(f"failed to generate search terms: {e}")
            search_terms = re.findall(r'\b\w+\b', video_script)[:5]

    if isinstance(search_terms, str):
        search_terms = [t.strip() for t in re.split(r"[,，]", search_terms)]
    search_terms = [t for t in search_terms if t]

    logger.info(f"script: {video_script[:200]}...")
    logger.info(f"search terms: {search_terms}")

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=45,
                         script=video_script, terms=search_terms,
                         log=_log(f"③ 文案改写完成，{len(video_script)} 字"))

    if stop_at == "script":
        sm.state.update_task(task_id, state=const.TASK_STATE_COMPLETE, progress=100,
                             script=video_script)
        return {"script": video_script, "terms": search_terms}

    # ── ④ TTS audio generation ──────────────────────────────────────
    if _is_stopped(task_id):
        return
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=50,
                         log=_log("④ 开始 TTS 配音..."))

    logger.info(f"\n## ④ generating audio (TTS)")
    audio_file = path.join(utils.task_dir(task_id), "audio.mp3")
    sub_maker = voice.tts(
        text=video_script,
        voice_name=voice.parse_voice_name(params.voice_name),
        voice_rate=params.voice_rate,
        voice_file=audio_file,
    )

    if sub_maker is None:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ TTS 配音失败"))
        logger.error("TTS generation failed")
        return

    audio_duration = math.ceil(voice.get_audio_duration(sub_maker))
    if audio_duration == 0:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ 无法获取音频时长"))
        logger.error("failed to get audio duration")
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=60,
                         audio_file=audio_file, audio_duration=audio_duration,
                         log=_log(f"④ 配音完成，时长 {audio_duration}s"))

    if stop_at == "audio":
        sm.state.update_task(task_id, state=const.TASK_STATE_COMPLETE, progress=100)
        return {"audio_file": audio_file, "audio_duration": audio_duration}

    # ── ⑤ Search video materials ────────────────────────────────────
    if _is_stopped(task_id):
        return
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=65,
                         log=_log("⑤ 搜索视频素材..."))

    material_searcher = _get_plugin(PluginType.MATERIAL, "material_provider")
    downloaded_videos = []

    if params.video_source != "local" and material_searcher:
        logger.info(f"\n## ⑤ searching materials from {params.video_source}")
        from app.models.schema import VideoAspect
        aspect = params.video_aspect or VideoAspect.portrait.value
        all_materials = []
        for term in search_terms:
            materials = material_searcher.search(
                query=term,
                video_aspect=aspect,
                min_duration=params.video_clip_duration or 5,
            )
            all_materials.extend(materials)

        # Download materials
        cache_dir = utils.storage_dir("cache_videos", create=True)
        for mat in all_materials:
            try:
                local_path = material_searcher.download(mat, cache_dir)
                if local_path:
                    downloaded_videos.append(local_path)
                    # Stop when we have enough duration
                    if len(downloaded_videos) * (params.video_clip_duration or 5) >= audio_duration * (params.video_count or 1):
                        break
            except Exception as e:
                logger.warning(f"failed to download material {mat.url}: {e}")

    logger.info(f"downloaded {len(downloaded_videos)} video materials")

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=75,
                         materials=downloaded_videos,
                         log=_log(f"⑤ 素材准备完成，{len(downloaded_videos)} 个视频"))

    if stop_at == "materials":
        sm.state.update_task(task_id, state=const.TASK_STATE_COMPLETE, progress=100)
        return {"materials": downloaded_videos}

    # ── ⑥ Compose final video ───────────────────────────────────────
    if _is_stopped(task_id):
        return
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=80,
                         log=_log("⑥ 开始合成视频..."))

    from app.services import video_rewrite
    logger.info(f"\n## ⑥ composing final video")

    # Generate subtitle if enabled
    subtitle_path = ""
    if params.subtitle_enabled and sub_maker is not None:
        subtitle_path = path.join(utils.task_dir(task_id), "subtitle.srt")
        voice.create_subtitle(
            text=video_script,
            sub_maker=sub_maker,
            subtitle_file=subtitle_path,
        )

    final_paths = []
    for i in range(params.video_count or 1):
        index = i + 1
        output_path = path.join(utils.task_dir(task_id), f"final-{index}.mp4")

        if downloaded_videos:
            # Compose from materials + new audio + subtitle
            result = video_rewrite.compose_from_materials(
                video_materials=downloaded_videos,
                audio_path=audio_file,
                subtitle_path=subtitle_path if os.path.isfile(subtitle_path) else "",
                output_path=output_path,
                params=params,
            )
        else:
            # Fallback: use source video + new audio + subtitle
            result = video_rewrite.replace_audio_track(
                video_path=video_pkg.video_path,
                audio_path=audio_file,
                subtitle_path=subtitle_path if os.path.isfile(subtitle_path) else "",
                output_path=output_path,
                params=params,
            )

        if result:
            final_paths.append(output_path)

        progress = 80 + int(20 / (params.video_count or 1) * index)
        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=progress)

    if not final_paths:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED,
                             log=_log("❌ 视频合成失败"))
        logger.error("video composition failed")
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=98,
                         log=_log(f"⑥ 视频合成完成，共 {len(final_paths)} 个"))

    # ── ⑦ (Optional) Publish ────────────────────────────────────────
    publish_results = []
    if params.auto_publish:
        publisher = _get_plugin(PluginType.PUBLISHER, "")
        if publisher:
            logger.info(f"\n## ⑦ publishing video")
            for vp in final_paths:
                result = publisher.publish(video_path=vp, title=video_script[:100])
                publish_results.append(result.model_dump() if hasattr(result, 'model_dump') else result)

    # ── Complete ─────────────────────────────────────────────────────
    kwargs = {
        "videos": final_paths,
        "script": video_script,
        "terms": search_terms,
        "audio_file": audio_file,
        "audio_duration": audio_duration,
        "subtitle_path": subtitle_path,
        "source_video": video_pkg.video_path,
    }
    if publish_results:
        kwargs["publish_results"] = publish_results

    sm.state.update_task(task_id, state=const.TASK_STATE_COMPLETE, progress=100,
                         log=_log(f"✅ 任务完成，生成 {len(final_paths)} 个视频"), **kwargs)
    logger.success(f"task {task_id} completed, generated {len(final_paths)} videos")
    return kwargs


def _get_plugin(plugin_type: PluginType, config_key: str):
    """Helper: instantiate the default or configured plugin for a type.

    Lazily imports all known plugin modules to trigger their
    __init_subclass__ auto-registration in PluginRegistry.
    """
    _ensure_plugins_imported(plugin_type)

    from app.config import config as app_config

    default_name = ""
    if config_key:
        default_name = getattr(app_config.app, config_key, "")

    plugin_cls = PluginRegistry.get_default(plugin_type, default_name)
    if plugin_cls is None:
        registered = PluginRegistry.list_plugins(plugin_type)
        logger.error(
            f"no plugin registered for {plugin_type.value} "
            f"(configured: {default_name!r}, registered: {registered})"
        )
        return None

    return plugin_cls()


def _ensure_plugins_imported(plugin_type: PluginType) -> None:
    """Import all modules under app/plugins/{type}/ to trigger auto-registration."""
    import importlib
    import pkgutil

    package_map = {
        PluginType.DOWNLOADER: "app.plugins.downloader",
        PluginType.TRANSCRIBER: "app.plugins.transcriber",
        PluginType.LLM: "app.plugins.llm",
        PluginType.MATERIAL: "app.plugins.material",
        PluginType.PUBLISHER: "app.plugins.publisher",
    }

    pkg_name = package_map.get(plugin_type)
    if not pkg_name:
        return

    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:
        return

    for _finder, mod_name, _ispkg in pkgutil.iter_modules(pkg.__path__, prefix=f"{pkg_name}."):
        # Skip __init__ and base modules — only import concrete implementations
        if mod_name.endswith("base") or mod_name == pkg_name:
            continue
        try:
            importlib.import_module(mod_name)
        except Exception as e:
            logger.warning(f"failed to import plugin module {mod_name}: {e}")
