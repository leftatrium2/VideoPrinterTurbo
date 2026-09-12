from sqlalchemy import Integer, REAL, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class VptAsrConfig(Base):
    __tablename__ = 'vpt_asr_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tencent_cloud_secret_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tencent_cloud_secret_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    xfyun_appid: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    xfyun_secret_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    xfyun_web_api: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    local_whisper_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    azure_subscription_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    azure_region: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    openai_api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    openai_model: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'whisper-1'"))
    openai_base_url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    volcengine_appid: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    volcengine_access_token: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    remote_whisper_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    remote_vllm_url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    remote_vllm_model: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    remote_whisper_cpp_url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptLlmConfig(Base):
    __tablename__ = 'vpt_llm_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    provider_name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    llm_model_name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    memo: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptProxyConfig(Base):
    __tablename__ = 'vpt_proxy_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proxy_server_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    proxy_server_url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    proxy_server_username: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    proxy_server_password: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptTasks(Base):
    __tablename__ = 'vpt_tasks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    create_time: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now', 'localtime')"))
    is_deleted: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    status: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    task_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    error_code: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    error_desc: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    is_rewrite_to_tts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_llm: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_publish: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_from_asr_or_subtitle: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    llm_prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    is_rewrite_to_subtitle: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_bgm: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_video_material: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    tts_speed: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    subtitle_size: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    uploaded_bgm: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    bgm_volume: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    video_material_type: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    uploaded_video_material: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    video_material_splicing_mode: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_material_transition_mode: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_material_video_ratio: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_material_max_duration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_material_generate_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    subtitle_font: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    subtitle_font_color: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    subtitle_border_color: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    audio_rewrite_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    tts_server: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tts_voice: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tts_volume: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    subtitle_position: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    subtitle_lang: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_download_proxy: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_material_keyword: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    task_upload_video_path: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    task_original_video_path: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptTtsConfig(Base):
    __tablename__ = 'vpt_tts_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tts_server: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    tts_voice: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tts_area: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tts_apikey: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptTtsVoiceConfig(Base):
    __tablename__ = 'vpt_tts_voice_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tts_server_name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tts_voice_content: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    tts_server_time: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptVideoConfig(Base):
    __tablename__ = 'vpt_video_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_source: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_joint_mode_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_transition_mode_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_ratio_type: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    video_fragment_duration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class VptVideoMaterialPexelsConfig(Base):
    __tablename__ = 'vpt_video_material_pexels_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pexels_api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))


class VptVideoMaterialPixabayConfig(Base):
    __tablename__ = 'vpt_video_material_pixabay_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pixabay_api_key: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
