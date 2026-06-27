# coding: utf-8
from sqlalchemy import Column, Float, Integer, Text, text
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
    task_id = Column(Integer, nullable=False, server_default=text("0"))
    error_code = Column(Integer, nullable=False, server_default=text("0"))
    error_desc = Column(Text, nullable=False, server_default=text("''"))
    is_rewrite_to_tts = Column(Integer, nullable=False, server_default=text("0"))
    is_llm = Column(Integer, nullable=False, server_default=text("0"))
    is_publish = Column(Integer, nullable=False, server_default=text("0"))
    is_from_asr_or_subtitle = Column(Integer, nullable=False, server_default=text("0"))
    tts_config_id = Column(Integer, nullable=False, server_default=text("0"))
    tts_voice_volume = Column(Float, nullable=False, server_default=text("1.0"))
    tts_voice_speed = Column(Float, nullable=False, server_default=text("1.0"))
    llm_prompt = Column(Text, nullable=False, server_default=text("''"))
    is_rewrite_to_subtitle = Column(Integer, nullable=False, server_default=text("0"))
    is_bgm = Column(Integer, nullable=False, server_default=text("0"))
    is_video_material = Column(Integer, nullable=False, server_default=text("0"))


class VptTtsConfig(Base):
    __tablename__ = 'vpt_tts_config'

    id = Column(Integer, primary_key=True)
    tts_server = Column(Integer, nullable=False, server_default=text("0"))
    tts_voice = Column(Text, nullable=False, server_default=text("''"))
    tts_area = Column(Text, nullable=False, server_default=text("''"))
    tts_apikey = Column(Text, nullable=False, server_default=text("''"))


class VptVideoConfig(Base):
    __tablename__ = 'vpt_video_config'

    id = Column(Integer, primary_key=True)
    video_source = Column(Integer, nullable=False, server_default=text("0"))
    video_joint_mode_type = Column(Integer, nullable=False, server_default=text("0"))
    video_transition_mode_type = Column(Integer, nullable=False, server_default=text("0"))
    video_ratio_type = Column(Integer, nullable=False, server_default=text("0"))
    video_fragment_duration = Column(Integer, nullable=False, server_default=text("0"))


class VptVideoMaterialConfig(Base):
    __tablename__ = 'vpt_video_material_config'

    id = Column(Integer, primary_key=True)
    pexels_api_keys = Column(Text, nullable=False, server_default=text("''"))
    pixabay_api_key = Column(Text, nullable=False, server_default=text("''"))
