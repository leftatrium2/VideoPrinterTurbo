# coding: utf-8
from sqlalchemy import Column, Float, Integer, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class VptAsrConfig(Base):
    __tablename__ = 'vpt_asr_config'

    id = Column(Integer, primary_key=True)
    tencent_cloud_secret_id = Column(Text, nullable=False, server_default=text("''"))
    tencent_cloud_secret_key = Column(Text, nullable=False, server_default=text("''"))
    xfyun_appid = Column(Text, nullable=False, server_default=text("''"))
    xfyun_secret_key = Column(Text, nullable=False, server_default=text("''"))
    xfyun_web_api = Column(Text, nullable=False, server_default=text("''"))
    local_whisper_type = Column(Integer, nullable=False, server_default=text("0"))
    aliyun_cloud_api_key = Column(Text, nullable=False, server_default=text("''"))
    aliyun_cloud_model = Column(Text, nullable=False, server_default=text("'paraformer-v2'"))
    azure_subscription_key = Column(Text, nullable=False, server_default=text("''"))
    azure_region = Column(Text, nullable=False, server_default=text("''"))
    openai_api_key = Column(Text, nullable=False, server_default=text("''"))
    openai_model = Column(Text, nullable=False, server_default=text("'whisper-1'"))
    openai_base_url = Column(Text, nullable=False, server_default=text("''"))
    volcengine_appid = Column(Text, nullable=False, server_default=text("''"))
    volcengine_access_token = Column(Text, nullable=False, server_default=text("''"))


class VptLlmConfig(Base):
    __tablename__ = 'vpt_llm_config'

    id = Column(Integer, primary_key=True)
    base_url = Column(Text, nullable=False, server_default=text("''"))
    api_key = Column(Text, nullable=False, server_default=text("''"))
    provider_name = Column(Text, nullable=False, server_default=text("''"))
    llm_model_name = Column(Text, nullable=False, server_default=text("''"))
    memo = Column(Text, nullable=False, server_default=text("''"))


class VptProxyConfig(Base):
    __tablename__ = 'vpt_proxy_config'

    id = Column(Integer, primary_key=True)
    proxy_server_type = Column(Integer, nullable=False, server_default=text("0"))
    proxy_server_url = Column(Text, nullable=False, server_default=text("''"))
    proxy_server_username = Column(Text, nullable=False, server_default=text("''"))
    proxy_server_password = Column(Text, nullable=False, server_default=text("''"))


class VptTask(Base):
    __tablename__ = 'vpt_tasks'

    id = Column(Integer, primary_key=True)
    task_url = Column(Text, nullable=False, server_default=text("''"))
    create_time = Column(Text, nullable=False, server_default=text("datetime('now', 'localtime')"))
    is_deleted = Column(Integer, nullable=False, server_default=text("0"))
    status = Column(Integer, nullable=False, server_default=text("0"))
    task_id = Column(Text, nullable=False, server_default=text("''"))
    error_code = Column(Integer, nullable=False, server_default=text("0"))
    error_desc = Column(Text, nullable=False, server_default=text("''"))
    is_rewrite_to_tts = Column(Integer, nullable=False, server_default=text("0"))
    is_llm = Column(Integer, nullable=False, server_default=text("0"))
    is_publish = Column(Integer, nullable=False, server_default=text("0"))
    is_from_asr_or_subtitle = Column(Integer, nullable=False, server_default=text("0"))
    llm_prompt = Column(Text, nullable=False, server_default=text("''"))
    is_rewrite_to_subtitle = Column(Integer, nullable=False, server_default=text("0"))
    is_bgm = Column(Integer, nullable=False, server_default=text("0"))
    is_video_material = Column(Integer, nullable=False, server_default=text("0"))
    tts_speed = Column(Float, nullable=False, server_default=text("0"))
    subtitle_size = Column(Integer, nullable=False, server_default=text("0"))
    uploaded_bgm = Column(Text, nullable=False, server_default=text("''"))
    bgm_volume = Column(Float, nullable=False, server_default=text("0"))
    video_material_type = Column(Text, nullable=False, server_default=text("''"))
    uploaded_video_material = Column(Text, nullable=False, server_default=text("''"))
    video_material_splicing_mode = Column(Integer, nullable=False, server_default=text("0"))
    video_material_transition_mode = Column(Integer, nullable=False, server_default=text("0"))
    video_material_Video_ratio = Column(Integer, nullable=False, server_default=text("0"))
    video_material_max_duration = Column(Integer, nullable=False, server_default=text("0"))
    video_material_generate_count = Column(Integer, nullable=False, server_default=text("0"))
    subtitle_font = Column(Text, nullable=False, server_default=text("''"))
    subtitle_font_color = Column(Integer, nullable=False, server_default=text("0"))
    subtitle_border_color = Column(Integer, nullable=False, server_default=text("0"))
    audio_rewrite_type = Column(Integer, nullable=False, server_default=text("0"))
    tts_server = Column(Text, nullable=False, server_default=text("''"))
    tts_voice = Column(Text, nullable=False, server_default=text("''"))
    tts_volume = Column(Float, nullable=False, server_default=text("0"))
    subtitle_position = Column(Text, nullable=False, server_default=text("''"))
    subtitle_lang = Column(Integer, nullable=False, server_default=text("0"))
    is_download_proxy = Column(Integer, nullable=False, server_default=text("0"))


class VptTtsConfig(Base):
    __tablename__ = 'vpt_tts_config'

    id = Column(Integer, primary_key=True)
    tts_server = Column(Integer, nullable=False, server_default=text("0"))
    tts_voice = Column(Text, nullable=False, server_default=text("''"))
    tts_area = Column(Text, nullable=False, server_default=text("''"))
    tts_apikey = Column(Text, nullable=False, server_default=text("''"))


class VptTtsVoiceConfig(Base):
    __tablename__ = 'vpt_tts_voice_config'

    id = Column(Integer, primary_key=True)
    tts_server_name = Column(Text, nullable=False, server_default=text("''"))
    tts_voice_content = Column(Text, nullable=False, server_default=text("''"))
    tts_server_time = Column(Text, nullable=False, server_default=text("''"))


class VptVideoConfig(Base):
    __tablename__ = 'vpt_video_config'

    id = Column(Integer, primary_key=True)
    video_source = Column(Integer, nullable=False, server_default=text("0"))
    video_joint_mode_type = Column(Integer, nullable=False, server_default=text("0"))
    video_transition_mode_type = Column(Integer, nullable=False, server_default=text("0"))
    video_ratio_type = Column(Integer, nullable=False, server_default=text("0"))
    video_fragment_duration = Column(Integer, nullable=False, server_default=text("0"))


class VptVideoMaterialPexelsConfig(Base):
    __tablename__ = 'vpt_video_material_pexels_config'

    id = Column(Integer, primary_key=True)
    pexels_api_key = Column(Text, nullable=False, server_default=text("''"))


class VptVideoMaterialPixabayConfig(Base):
    __tablename__ = 'vpt_video_material_pixabay_config'

    id = Column(Integer, primary_key=True)
    pixabay_api_key = Column(Text, nullable=False, server_default=text("''"))
