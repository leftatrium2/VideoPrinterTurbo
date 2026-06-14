# coding: utf-8
from sqlalchemy import Column, Float, Integer, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


t_sqlite_sequence = Table(
    'sqlite_sequence', metadata,
    Column('name', NullType),
    Column('seq', NullType)
)


class VptLlmConfig(Base):
    __tablename__ = 'vpt_llm_config'

    id = Column(Integer, primary_key=True)
    base_url = Column(Text, nullable=False, server_default=text("''"))
    apk_key = Column(Text, nullable=False, server_default=text("''"))
    llm_name = Column(Text, nullable=False, server_default=text("''"))
    llm_model_name = Column(Text, nullable=False, server_default=text("''"))


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


class VptTtsConfig(Base):
    __tablename__ = 'vpt_tts_config'

    id = Column(Integer, primary_key=True)
    tts_server = Column(Text, nullable=False, server_default=text("''"))
    tts_voice = Column(Text, nullable=False, server_default=text("0"))
    tts_voice_volume = Column(Float, nullable=False, server_default=text("1.0"))
    tts_voice_speed = Column(Float, nullable=False, server_default=text("1.0"))


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
